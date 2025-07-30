import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiofiles
from neo4j import (
    AsyncGraphDatabase,
)
from neo4j import (
    exceptions as neo4jExceptions,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from ragchat.definitions import (
    Flow,
    IndexedFilters,
    Node,
    NodeType,
    Point,
    Relation,
    indexed_keys,
    search_space_key,
)
from ragchat.log import DEBUG, abbrev, get_logger
from ragchat.utils import remove_keys, retry, timeit

notifications_logger = logging.getLogger("neo4j.notifications")
notifications_logger.setLevel(logging.ERROR)
logger = get_logger(__name__)


class Neo4jSettings(BaseSettings):
    url: Optional[str] = None
    local_hosts: Optional[List[str]] = ["localhost", "host.docker.internal"]
    bolt_port: int = 7687
    user: str
    password: str
    pool_size: int = 100
    timeout: int = 30
    acq_timeout: int = 60
    retry_time: int = 30

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="NEO4J_")

    async def initialize(self) -> None:
        """
        Attempts to connect to Neo4j using the provided URL or default local hosts.
        Sets the `url` attribute to the first successful connection URL.
        Raises ConnectionError if no connection can be established.
        """
        urls_to_check = set()
        if self.url:
            urls_to_check.add(self.url)

        for host in self.local_hosts or []:
            urls_to_check.add(f"bolt://{host}:{self.bolt_port}")

        connection_attempts = [self._attempt_connection(url) for url in urls_to_check]
        results = await asyncio.gather(*connection_attempts, return_exceptions=True)
        successful_results = [result for result in results if isinstance(result, str)]
        self.url = next((result for result in successful_results if result), None)
        if not self.url:
            raise ConnectionError(
                f"Could not connect to Neo4j using any of the default hosts or the provided URL: {self.url}"
            )

        logger.info(f"Connection established using {self.url.split('@')[-1]}")

    async def _attempt_connection(self, url: str) -> str | None:
        """Attempts to connect to Neo4j at the given URL and returns the URL if successful."""
        try:
            driver = AsyncGraphDatabase.driver(url, auth=(self.user, self.password))
            async with driver:
                await driver.verify_connectivity()
            await driver.close()
            return url
        except Exception as e:
            logger.debug(f"Failed to connect to {url}: {e}")
            return None


class Neo4j:
    """
    Manages interactions with a Neo4j graph database, including node and relation operations, indexing, and search.
    """

    def __init__(self, settings: Optional[Neo4jSettings] = None):
        self.settings = settings or Neo4jSettings()
        self.retry_on = [  # only retry on these errors
            neo4jExceptions.TransientError,
            neo4jExceptions.ServiceUnavailable,
            neo4jExceptions.DatabaseError,
        ]

    async def initialize(self) -> None:
        """Initializes the Neo4j database with necessary constraints and indexes."""
        await self.settings.initialize()
        assert self.settings.url, "Missing settings.url"
        self.graph = AsyncGraphDatabase.driver(
            self.settings.url,
            auth=(self.settings.user, self.settings.password),
            max_connection_pool_size=self.settings.pool_size,
            connection_timeout=self.settings.timeout,
            connection_acquisition_timeout=self.settings.acq_timeout,
            max_transaction_retry_time=self.settings.retry_time,
        )

        queries = [
            f"create index idx_{NodeType.CHUNK}_{k} if not exists for (n:{NodeType.CHUNK}) on (n.search_space, n.{k});"
            for k in (indexed_keys() - {"node_id", "search_space"})
        ]
        queries += [
            f"create index idx_{node_type}_node_id if not exists for (n:{node_type}) on (n.node_id);"
            for node_type in [NodeType.CHUNK, NodeType.ENTITY]
        ]

        async with self.graph.session() as session:
            for q in queries:
                await session.run(q)
            logger.info("Neo4j initialized successfully.")

    def _get_filter_clause(
        self,
        indexed_filters: IndexedFilters,
        node_type: NodeType,
        node_letter: str = "n",
        exclude_with: bool = False,
    ) -> str:
        """
        Build a Neo4j filter clause string based on provided filters.
        """
        filter_clause_str = ""
        assert indexed_filters.flow
        filter_clauses = [
            f"{node_letter}.{k} {condition.operator} $filters.{k}"
            for k, v in indexed_filters.std_conditions().items()
            for condition in v
            if k in Node.node_keys(node_type, indexed_filters.flow)
        ]

        if not filter_clauses:
            raise ValueError("Missing filter.")

        filter_clause_str += f"""
            {"" if exclude_with else "with *"}
            where """ + """
            and """.join(filter_clauses)

        if not node_type == NodeType.CHUNK:
            return filter_clause_str
        if exclude_with:
            raise ValueError(f"Cannot exclude_with for {NodeType.CHUNK} nodes.")

        filter_clauses = [
            f"custom.{k} {condition.operator} $filters.{k}"
            for k, v in indexed_filters.std_conditions().items()
            for condition in v
            if k not in Node.node_keys(node_type, indexed_filters.flow)
        ]

        if not filter_clauses:
            return filter_clause_str

        filter_clause_str += f"""
            with *, apoc.convert.fromJsonMap({node_letter}.custom) as custom
            where """ + """
            and """.join(filter_clauses)

        return filter_clause_str

    def _get_cleanup_clause(
        self,
        node_type: NodeType,
        node_letter: str = "n",
    ) -> str:
        """
        Generates a Cypher clause to identify and collect nodes for deletion,
        including primary nodes and any related nodes that become orphaned.

        Args:
            node_type: The NodeType of the primary nodes being deleted.
            node_letter: The variable name for the primary nodes being deleted.

        Returns:
            str: Cypher clause for identifying and collecting nodes for deletion.

        NOTE: Assumes insertion *after* a MATCH clause for primary nodes
              and *before* the final `DETACH DELETE`.
        """
        label = node_type.value  # Get the string label from NodeType
        n = node_letter  # alias for node_letter for readability
        r = f"""
            // Collect the original nodes identified for deletion
            with collect({n}) as x_nodes                                    // nodes being deleted
            with x_nodes as {n}_nodes, x_nodes                              // keep a pointer to the original nodes

            // 1. From first-degree adjacent nodes
            optional match (x)
            where not x:{label}                                             // Is not the node_type being deleted
            and exists((x)--(:{label}))                                     // Has connection to the node_type being deleted
            and all(y in [(x)--(z:{label}) | z] where y in x_nodes)         // Their only {label} connections are to nodes being deleted
            with {n}_nodes, x_nodes, x where x is not null                  // filter out nulls
            with {n}_nodes, x_nodes, collect(distinct x) as _nodes
            with {n}_nodes, x_nodes + _nodes as x_nodes                     // combine nodes being deleted

            // 2. From first/second-degree adjacent nodes
            optional match (x)
            where not x:{label}                                             // Is not the node_type being deleted
            and not any(y in [(x)--(z) | z] where not y in x_nodes)         // Connected only to nodes being deleted
            with {n}_nodes, x_nodes, x where x is not null                  // filter out nulls
            with {n}_nodes, x_nodes, collect(distinct x) as _nodes
            with {n}_nodes, x_nodes + _nodes as x_nodes                     // combine nodes being deleted

            // 3. Get unique set of nodes to delete
            with apoc.coll.toSet({n}_nodes + x_nodes) as {n}_nodes
            unwind {n}_nodes as {n}
        """

        return r

    def _get_projection(
        self,
        return_fields: Optional[set[str]] = None,
        node_letter: str = "n",
        include: Optional[set[str]] = None,
        exclude: Optional[set[str]] = None,
    ) -> Dict[str, str]:
        """
        Generates a Cypher projection dictionary for returning node properties.

        Args:
            return_fields: Set of fields to include in the projection.
            node_letter: The variable name used for the node in the Cypher query.
            include: Set of fields to always include.
            exclude: Set of fields to always exclude.

        Returns:
            Dict[str, str]: The Cypher projection as a dictionary.
        """
        unpack: bool = not return_fields
        return_fields = (return_fields or {"custom"}) - (exclude or set()) | (
            include or set()
        )

        r = {field: f"{node_letter}.{field}" for field in return_fields}
        r |= {
            k: v
            for k, v in {
                "custom": f"case when {node_letter}.custom is not null then apoc.convert.fromJsonMap({node_letter}.custom) else null end",
                "similarity": "similarity",
                "explain": "explain",
                "types": "types",
            }.items()
            if k in return_fields
        }
        if unpack and exclude:
            r |= {k: "null" for k in exclude}

        return r

    def _get_projection_map_str(
        self,
        return_fields: Optional[set[str]] = None,
        node_letter: str = "n",
        include: Optional[set[str]] = None,
        exclude: Optional[set[str]] = None,
    ) -> str:
        """
        Generates a Cypher map projection string for returning node properties.

        Args:
            return_fields: Set of fields to include in the projection. If None, includes all properties.
            node_letter: The variable name used for the node in the Cypher query.
            include: Set of fields to always include.
            exclude: Set of fields to always exclude.

        Returns:
            str: The Cypher map projection string.
        """
        include = (
            (include or set())
            | {"node_type", "flow", "content"}
            | {search_space_key(flow) for flow in Flow}
        )
        unpack = ".*, " if not return_fields else ""
        r = self._get_projection(return_fields, node_letter, include, exclude)
        projection_str = ", ".join([f"{k}: {v}" for k, v in r.items()])
        result = node_letter + "{" + unpack + projection_str + "}"
        return result

    @retry(retries=5)
    async def upsert_relation(
        self,
        relation: Relation,
    ) -> Relation:
        """
        Adds or updates a relation and its associated nodes in the graph.

        Merges nodes based on `node_id` or creates new ones. Sets properties and creates/merges relationships.

        Args:
            relation: A Relation object to upsert.

        Returns:
            Relation: The upserted relation with updated node_ids for newly created nodes.
        """
        logger.debug(f"upserting relation: {abbrev(relation)}")
        exclude = {"embeddings"}

        # --- build cypher ---
        nodes = relation.to_list(include=[NodeType.CHUNK, NodeType.ENTITY])
        parameters = {
            f"n{i}": n.model_dump(mode="json", exclude=exclude)
            for i, n in enumerate(nodes)
        }

        match_create_clauses = []
        # match or create clauses
        for i, n in enumerate(nodes):
            with_clause = "with *" if i > 0 else ""
            if n.node_id:
                match_create_clauses.append(
                    f"{with_clause} merge (n{i}:{n.node_type} {{node_id: $n{i}.node_id}})"
                )
            else:
                match_create_clauses.append(
                    f"{with_clause} create (n{i}:{n.node_type})"
                )

        # set properties clauses
        set_clauses = []
        for i, n in enumerate(nodes):
            weird_fields = {
                "node_id": f"n{i}.node_id = coalesce(n{i}.node_id, randomUUID())",
                "created_at": f"n{i}.created_at = coalesce(n{i}.created_at, timestamp())",
                "updated_at": f"n{i}.updated_at = timestamp()",
                "custom": f"n{i}.custom = case when coalesce($n{i}.custom, n{i}.custom) is not null then apoc.convert.toJson(coalesce($n{i}.custom, n{i}.custom)) else null end",
            }

            set_clause = [
                f"n{i}.{k} = coalesce($n{i}.{k}, n{i}.{k})"
                if k not in weird_fields
                else weird_fields[k]
                for k in n.this_node_keys() - exclude
            ]
            set_str = """,
                """.join(set_clause)

            set_clauses.append(f"""
            set
                {set_str}
            """)

        # relation clauses
        # entity-[fact]->chunk
        relation_clauses = []
        for i, n in enumerate(nodes):
            if i == 0 and n.file_id:
                relation_clauses.append(
                    f"""
                    with *
                    optional match (prev_n0:{NodeType.CHUNK} {{file_id: $n0.file_id}})
                    where apoc.convert.fromJsonMap(prev_n0.custom).ichunk = $n0.custom.ichunk - 1
                    foreach (_ in case when prev_n0 is not null then [1] else [] end | merge (prev_n0)-[:{NodeType.CHUNK}_{NodeType.CHUNK}]->(n0))
                    """
                )
            else:
                relation_clauses.append(
                    f"merge (n{i})-[:{NodeType.ENTITY}_{NodeType.CHUNK}]->(n0)"
                )

        # return clauses
        return_clauses = [f"n{i}.node_id" for i in range(len(nodes))]

        # Combine all parts
        cypher = "\n".join(match_create_clauses)
        cypher += "\n" + "\n".join(set_clauses)
        cypher += "\n" + "\n".join(relation_clauses)
        cypher += "\nreturn " + ", ".join(return_clauses)
        cypher_lines = cypher.splitlines()
        stripped_lines = [line.strip() for line in cypher_lines]
        cypher = "\n".join(stripped_lines)

        # Execute the Cypher query
        try:
            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)
                data = await result.data()
                if data:
                    for i, n in enumerate(nodes):
                        n.node_id = data[0][f"n{i}.node_id"]
                        assert n.node_id, "Missing node_id"

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nParameters: {abbrev(parameters)}")
            raise

        return relation

    @retry()
    async def get_nodes_by_ids(
        self,
        node_ids: List[str],
        node_type: NodeType = NodeType.CHUNK,
        return_fields: Optional[set[str]] = None,
    ) -> List[Node]:
        """
        Retrieves multiple nodes by their IDs.

        Args:
            node_ids: List of node IDs to retrieve.
            node_type: Type of node to retrieve (default: CHUNK).
            return_fields: Fields to return for each node.

        Returns:
            List[Node]: The retrieved nodes (empty list if none found).
        """
        if not node_ids:
            return []

        cypher = f"""
            match (n:{node_type})
            where n.node_id in $node_ids
            return {self._get_projection_map_str(return_fields)}
        """

        try:
            parameters = {"node_ids": node_ids}

            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)
                records = await result.data()

            if not records:
                logger.debug(f"No {node_type} nodes found with IDs {node_ids}")
                return []

            nodes = []
            for record in records:
                nodes.append(Node(**record["n"]))

            return nodes

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nParameters: {abbrev(parameters)}")
            raise

    @retry()
    async def get_nodes(
        self,
        indexed_filters: IndexedFilters,
        node_type: NodeType = NodeType.CHUNK,
        return_fields: Optional[set[str]] = None,
        order_by: str = "updated_at",
        order_direction: str = "desc",
        limit: int = 100,
    ) -> List[Node]:
        """
        Retrieves nodes of a specific type with filtering and ordering.

        Args:
            indexed_filters: Filters to apply to the query.
            node_type: Type of node to retrieve (default: CHUNK).
            return_fields: Fields to return for each node.
            order_by: Property to order results by (default: "updated_at").
            order_direction: Direction of ordering, "asc" or "desc" (default: "desc").
            limit: Maximum number of nodes to return (default: 100).

        Returns:
            List[Node]: The retrieved nodes (empty list if none found).
        """
        if order_by not in ["created_at", "updated_at"]:
            raise ValueError(f"order_by must be a valid field, order_by: {order_by}")
        if order_direction not in ["asc", "desc"]:
            raise ValueError(
                f"order_direction must be a valid direction, order_direction: {order_direction}"
            )
        if not indexed_filters:
            raise ValueError("Missing filters.")

        # Add ordering if specified
        order_clause = ""
        if order_by:
            order_clause = f"order by n.{order_by} {order_direction}"

        # Add limit if specified
        limit_clause = ""
        if limit is not None:
            limit_clause = f"limit {limit}"

        cypher = f"""
            match (n:{node_type})
            {self._get_filter_clause(indexed_filters, node_type, "n")}
            {order_clause}
            {limit_clause}
            return {self._get_projection_map_str(return_fields)}
        """

        try:
            parameters = {"filters": indexed_filters.std_dict()}

            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)
                records = await result.data()

            if not records:
                logger.debug(f"No {node_type} nodes found with the specified criteria")
                return []

            nodes = []
            for record in records:
                nodes.append(Node(**record["n"]))

            return nodes

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nParameters: {abbrev(parameters)}")
            raise

    @retry()
    async def get_updated_at(
        self,
        indexed_filters: IndexedFilters,
        return_fields: Optional[set[str]] = None,
        order_by: Optional[str] = "updated_at",
        order_direction: Optional[str] = "desc",
        limit: Optional[int] = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the latest 'updated_at' timestamp for nodes matching filters, grouped by return fields.

        Args:
            indexed_filters: Filters to apply to the query.
            return_fields: Fields to group by and return along with the max updated_at. Defaults to indexed keys.
            limit: Maximum number of results to return (default: 100)
            order_by: Property to order results by ('created_at' or 'updated_at', default: 'updated_at')
            order_direction: Direction of ordering, "asc" or "desc" (default: "desc")
        """
        if not indexed_filters:
            raise ValueError("Missing filters.")
        if order_by and order_by not in ["created_at", "updated_at"]:
            raise ValueError(f"order_by must be a valid field, order_by: {order_by}")
        if order_direction and order_direction not in ["asc", "desc"]:
            raise ValueError(
                f"order_direction must be a valid direction, order_direction: {order_direction}"
            )

        order_clause = ""
        if order_by:
            order_clause = f"order by n.{order_by} {order_direction}"

        limit_clause = ""
        if limit is not None:
            limit_clause = f"limit {limit}"

        return_fields = return_fields or indexed_keys(indexed_filters.flow)
        projection = ", ".join([
            f"{v} as {k}"
            for k, v in self._get_projection(return_fields, include=None).items()
        ])

        node_type = NodeType.CHUNK
        cypher = f"""
            match (n:{node_type})
            {self._get_filter_clause(indexed_filters, node_type, "n")}
            return {projection}, max(n.updated_at) as updated_at
            {order_clause}
            {limit_clause}
        """

        try:
            parameters = {"filters": indexed_filters.std_dict()}

            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)
                records = await result.data()

            if not records:
                logger.debug("No chunk nodes found with the specified criteria")
                return []

            return records

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nParameters: {abbrev(parameters)}")
            raise

    @retry()
    async def update_nodes_by_ids(
        self,
        nodes: List[Node],
        return_fields: Optional[set[str]] = None,
    ) -> List[Node]:
        """
        Updates multiple nodes by their IDs, preserving existing properties when new values are null.

        Args:
            nodes: List of Node objects with updated properties.
            return_fields: Fields to return for the updated nodes.

        Returns:
            List[Node]: The updated nodes (empty list if none found).
        """
        if not nodes:
            return []

        node_data = []
        for node in nodes:
            properties = node.model_dump(
                mode="json", exclude={"node_id", "node_type", "flow"}
            )
            node_data.append({
                "node_id": node.node_id,
                "node_type": node.node_type,
                "flow": node.flow,
                "properties": {k: v for k, v in properties.items()},
            })

        cypher = f"""
            unwind $node_data as data
            match (n:data.flow:data.node_type)
            where n.node_id = data.node_id

            set n = apoc.map.merge(n, data.properties, {{
                // For each property in the update, use coalesce to keep existing value if new is null
                // k, v -> case when v is null then n[k] else v end
                k, v -> coalesce(v, n[k])
            }})

            return {self._get_projection_map_str(return_fields)}
        """

        try:
            parameters = {"node_data": node_data}

            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)
                records = await result.data()

            if not records:
                logger.debug("No nodes found with the provided IDs")
                return []

            updated_nodes = []
            for record in records:
                updated_nodes.append(Node(**record["n"]))

            return updated_nodes

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nParameters: {abbrev(parameters)}")
            raise

    @retry()
    async def delete_nodes_by_ids(
        self,
        node_ids: List[str],
        node_type: NodeType = NodeType.CHUNK,
        return_fields: Optional[set[str]] = None,
        cleanup: bool = True,
    ) -> List[Node]:
        """
        Deletes multiple nodes by their IDs.

        Args:
            node_ids: List of node IDs to delete.
            node_type: Type of node to delete (default: CHUNK).
            return_fields: Fields to return for the deleted nodes.
            cleanup: Whether to perform cleanup operations on orphaned nodes.

        Returns:
            List[Node]: The deleted nodes (empty list if none found).
        """
        if not node_ids:
            return []
        projection = self._get_projection_map_str(return_fields)[1:]

        cypher = f"""
            match (n:{node_type})
            where n.node_id in $node_ids
            {self._get_cleanup_clause(node_type, "n") if cleanup else ""}
            with n, {projection} as r
            detach delete n
            return r
        """

        try:
            parameters = {"node_ids": node_ids}

            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)
                records = await result.data()

            if not records:
                logger.debug(f"No {node_type} nodes found with the specified criteria")
                return []

            nodes = [Node(**r["r"]) for r in records]

            return nodes

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nParameters: {abbrev(parameters)}")
            raise

    @retry()
    async def delete_nodes(
        self,
        indexed_filters: IndexedFilters,
        node_type: NodeType = NodeType.CHUNK,
        return_fields: Optional[set[str]] = None,
        cleanup: bool = True,
    ) -> List[Node]:
        """
        Deletes nodes based on filters.

        Args:
            indexed_filters: Filters to apply to the query (required).
            node_type: Type of node to delete (default: CHUNK).
            return_fields: Fields to return for the deleted nodes.
            cleanup: Whether to run cleanup operations for orphaned nodes (default: True).

        Returns:
            List[Node]: The deleted nodes (empty list if none found).
        """
        if not indexed_filters:
            raise ValueError("Missing filters.")

        projection = self._get_projection_map_str(return_fields)

        cypher = f"""
            match (n:{node_type})
            {self._get_filter_clause(indexed_filters, node_type, "n")}
            {self._get_cleanup_clause(node_type, "n") if cleanup else ""}
            with n, {projection} as r
            detach delete n
            return r
        """

        try:
            parameters = {"filters": indexed_filters.std_dict()}

            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)
                records = await result.data()

            if not records:
                logger.debug(f"No {node_type} nodes found with the specified criteria")
                return []

            nodes = [Node(**r["r"]) for r in records]

            return nodes

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nParameters: {abbrev(parameters)}")
            raise

    @retry()
    @timeit(log_level=DEBUG, laps=1)
    async def search_chunks_from_points(
        self,
        points: List[Point],
        indexed_filters: IndexedFilters,
        threshold: float,
        limit: int = 128,
        char_limit: int = 12000,  # ~ 3k tokens (ollama default max 4k)
        max_hops: int = 3,
        explain: bool = False,
        profile: bool = False,
        return_fields: Optional[set[str]] = None,
    ) -> List[Node]:
        """
        Searches for relevant chunk nodes connected to input points using vector similarity.
        Results are weighted and reranked based on similarity and node type connections.

        Args:
            points: A list of Point objects representing the starting nodes for the search.
            indexed_filters: Filters to apply to the search (applied to both input nodes and resulting chunks).
            threshold: The minimum similarity score required for related nodes.
            limit: Maximum number of chunk nodes to return.
            char_limit: Maximum total character count for the returned chunks.
            max_hops: Maximum number of hops for path search between entities and chunks.
            explain: If True, includes explanation details in the returned nodes.
            profile: If True, profiles the Cypher query.
            return_fields: Fields to return for each chunk node.

        Returns:
            List[Node]: A list of relevant chunk nodes, limited by count and character limit,
                        and sorted by custom index ('ichunk') and creation time.
        """
        if not points:
            return []
        if not indexed_filters:
            raise ValueError("Missing filters.")

        include = {"similarity"}
        if explain:
            include |= {"explain"}

        projection = self._get_projection_map_str(
            return_fields, node_letter="c", include=include
        )

        cypher = f"""
            {"PROFILE" if profile else ""}
            // get matching nodes in a single collection
            with $entry_points as ps

            call (ps) {{
                unwind ps as p
                optional match (c:{NodeType.CHUNK})
                where c.node_id = p.node_id
                
                optional match (e:{NodeType.ENTITY})
                where e.node_id = p.node_id
                
                with p, c, e
                with p,
                     case when c is not null then [
                         {{c: c, s: p.similarity
                             {', explain: tostring(round(p.similarity * 1000.0) / 1000.0)+"=("+p.query_content+"<=>"+c.content+")"' if explain else ""}
                         }}
                     ] else [] end +
                     case when e is not null then [
                         {{e: e, s: p.similarity, q: p.query_content, g: p.group_id
                             {' , explain: tostring(round(p.similarity * 1000.0) / 1000.0)+"=("+p.query_content+"<=>"+e.content+")"' if explain else ""}
                         }}
                     ] else [] end as ns
                return apoc.coll.flatten(collect(ns)) as nss
            }}
            // cross join chunks and entitites
            with
                [ns in nss where ns.e.node_type = '{NodeType.ENTITY}' | ns] as ess,
                [ns in nss where ns.c.node_type = '{NodeType.CHUNK}' | ns] as css
            unwind ess as es
            unwind css as cs

            // entity multihop path search
            with *, cs.c as c, es.e as e
            match shortestPath((e)-[r*1..{max(1, max_hops)}]-(c))
            with *, size(r) as hops
            
            with cs, es{{.*,
                s: (es.s)^sqrt(hops)
                {', explain: tostring(round(es.s^(sqrt(hops)) * 1000.0) / 1000.0)+"=("+es.explain+")^sqrt(hops="+hops+")"' if explain else ""}
            }}
            where $threshold <= es.s
            order by es.s desc
            with cs, es.g as group_id, collect(es)[0] as es

            // get weighted avg similarity -- tweaked geometric mean
            with cs.c as c, (max(cs.s) + apoc.agg.product(es.s)^(3.0/count(es.s))) as similarity
            {", {c: collect({s: cs.s, explain: cs.explain})[0], e: collect({s: es.s, explain: es.explain})} as explain" if explain else ""}
            order by similarity desc
            limit $limit
            
            return {projection}
            """

        if profile or explain:
            logger.info(f"cypher: {cypher}")

        async def _get_records(
            entry_points: List[Point],
            explain: bool,
            profile: bool,
        ) -> List[Dict[str, Any]]:
            parameters = {
                "entry_points": [p.model_dump(mode="json") for p in entry_points],
                "filters": indexed_filters.std_dict() if indexed_filters else {},
                "threshold": threshold,
                "limit": limit,
            }
            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)
                raw_records = await result.data()

                if profile:
                    summary = await result.consume()
                    logger.info(f"Profile {summary.profile}")
                if explain:
                    cleaned_records = [
                        remove_keys(r, {"embeddings", "content"}) for r in raw_records
                    ]
                    logger.info(
                        "Records (%d): %s",
                        len(raw_records),
                        json.dumps(cleaned_records, indent=2),
                    )
                if profile or explain:
                    logger.info(f"Returned ({len(raw_records)}) records.")

            processed_records = [record["c"] for record in raw_records]

            return processed_records

        try:
            results_list = await _get_records(points, explain, profile)
            if not results_list:
                return []
            limited_records = self._limit_records(results_list, limit, char_limit)
            chunks = [Node(**r) for r in limited_records]
            # final sort
            chunks.sort(
                key=lambda x: (x.file_id, (x.custom or {}).get("ichunk"), x.updated_at)
            )

            return chunks

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nFilters {indexed_filters}")
            raise

    def _limit_records(
        self, records: List[Dict[str, Any]], limit: int, char_limit: int
    ) -> List[Dict[str, Any]]:
        """
        Deduplicates records by node_id (keeping the one with highest similarity),
        sorts them by similarity, and limits the number of records and the total
        character count of their content.

        Assumes 'node_id', 'similarity', and 'content' are top-level keys in each record dict.

        Args:
            records: The list of raw record dictionaries.
            limit: The maximum number of records to return after deduplication and sorting.
            char_limit: The maximum total character count allowed across all returned nodes.

        Returns:
            list[dict]: The limited list of record dictionaries.
        """
        # Deduplicate records by node_id, keeping the one with the highest similarity
        deduplicated_map: Dict[str, Dict[str, Any]] = {}
        for r in records:
            node_id = r.get("node_id")
            if not node_id:
                continue  # Skip records without a valid node_id

            similarity = r.get("similarity", 0.0)

            # Keep the record with the highest similarity for this node_id
            if node_id not in deduplicated_map or similarity > deduplicated_map[
                node_id
            ].get("similarity", 0.0):
                deduplicated_map[node_id] = r

        deduplicated_records = list(deduplicated_map.values())

        # Sort deduplicated records by similarity in descending order
        deduplicated_records.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        # Apply limit and character limit
        limited_records = []
        chars = 0
        for i, r in enumerate(deduplicated_records):
            # Apply the record limit
            if i >= limit:
                break

            # Get content safely
            content = r.get("content", "")
            content_len = len(content)

            # Apply character limit
            if char_limit > 0 and chars + content_len > char_limit:
                break

            limited_records.append(r)
            chars += content_len

        return limited_records

    @retry()
    async def export(
        self,
        file_name: str,
        indexed_filters: IndexedFilters,
        order_by: str = "updated_at",
        order_direction: str = "asc",
        return_fields: Optional[set[str]] = None,
    ) -> None:
        """
        Dumps all nodes matching filters to a file, streaming the results to avoid loading everything into memory.

        Args:
            file_name: The name of the file to write to.
            indexed_filters: Filters to apply to the query.
            order_by: Property to order results by (default: 'updated_at').
            order_direction: Direction of ordering, "asc" or "desc" (default: "asc").
            return_fields: Fields to return for each node.
        """
        if not indexed_filters:
            raise ValueError("Missing filters.")
        if order_by not in ["created_at", "updated_at"]:
            raise ValueError(f"order_by must be a valid field, order_by: {order_by}")
        if order_direction not in ["asc", "desc"]:
            raise ValueError(
                f"order_direction must be a valid direction, order_direction: {order_direction}"
            )

        # Add ordering if specified
        order_clause = ""
        if order_by:
            order_clause = f"order by n.{order_by} {order_direction}"

        clauses = [
            f"""
            match (n:{node_type})
            {self._get_filter_clause(indexed_filters, node_type, "n")}
            {order_clause}
            return {self._get_projection_map_str(return_fields)}
            """
            for node_type in NodeType
        ]

        cypher = "union".join(clauses)

        try:
            parameters = {"filters": indexed_filters.std_dict()}

            async with self.graph.session() as session:
                result = await session.run(cypher, parameters=parameters)

                async with aiofiles.open(file_name, "w") as f:
                    async for record in result:
                        node = Node(**record["n"])
                        await f.write(
                            node.model_dump_json() + "\n"
                        )  # Write each node as a JSON string on a new line

            logger.info(f"Successfully exported nodes to {file_name}")

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(f"Query:\n{cypher},\nParameters: {abbrev(parameters)}")
            raise

    async def drop_indexes(self, idxs: Optional[set[str]] = None) -> None:
        """
        Drops existing 'idx_' prefixed indexes from the database.

        If `idxs` is provided, only those specific indexes are dropped.
        Otherwise, all 'idx_' prefixed indexes are dropped.

        Args:
            idxs: An optional set of specific index names to drop.
        """
        logger.info("Dropping previous indexes...")

        try:
            async with self.graph.session() as session:
                result = await session.run("show indexes")
                records = await result.data()
                existing_indexes = [record["name"] for record in records]

                drop_queries = []
                for index_name in existing_indexes:
                    if index_name.startswith("idx_") and (
                        idxs is None or index_name in idxs
                    ):
                        drop_queries.append(f"drop index {index_name} if exists;")

                if drop_queries:
                    logger.info(
                        f"Found {len(drop_queries)} indexes to drop. Dropping..."
                    )
                    for query in drop_queries:
                        try:
                            await session.run(query)
                            logger.debug(f"Dropped index: {query}")
                            await asyncio.sleep(0.1)
                        except Exception as e:
                            logger.error(f"Failed to drop index '{query}': {e}")
                    logger.info("Previous indexes dropped.")
                else:
                    if idxs:
                        logger.info(
                            f"No specified 'idx_' prefixed indexes found to drop from {idxs}."
                        )
                    else:
                        logger.info("No 'idx_' prefixed indexes found to drop.")

        except Exception as e:
            logger.error(f"Error during index drop process: {e}")
            raise

    async def close(self) -> None:
        """Closes the Neo4j graph driver connection."""
        await self.graph.close()
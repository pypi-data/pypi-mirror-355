import asyncio
import math
import uuid
from typing import Dict, Hashable, List, Optional, Sequence, Set, Type, cast

import numpy as np
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client import AsyncQdrantClient, models
from rapidfuzz import distance, fuzz
from sklearn.cluster import KMeans

from ragchat.definitions import (
    Embedding,
    EmbeddingType,
    Id,
    IndexedFilters,
    NodeType,
    Operator,
    Point,
    QueryPoint,
    Relation,
    decode_kv,
    encode_kv,
)
from ragchat.log import DEBUG, abbrev, get_logger
from ragchat.parser import split_name_descriptor
from ragchat.utils import is_iso_datetime_string, rescale_similarity, retry, timeit

logger = get_logger(__name__)


class QdrantSettings(BaseSettings):
    url: Optional[str] = None
    local_hosts: Optional[List[str]] = ["localhost", "host.docker.internal"]
    port: int = 6333
    grpc_port: int = 6334
    p2p_port: int = 6335
    api_key: Optional[str] = None
    idx_on_disk: bool = True
    vec_on_disk: bool = True
    quantile: float = 0.99

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="QDRANT_")

    async def initialize(self) -> None:
        """
        Attempts to connect to Qdrant using the provided URL or default local hosts.
        Sets the `url` attribute to the first successful connection URL.
        Raises ConnectionError if no connection can be established.
        """
        urls_to_check = set()
        if self.url:
            urls_to_check.add(self.url)

        for host in self.local_hosts or []:
            urls_to_check.add(f"http://{host}:{self.port}")

        connection_attempts = [self._attempt_connection(url) for url in urls_to_check]
        results = await asyncio.gather(*connection_attempts, return_exceptions=True)
        successful_results = [result for result in results if isinstance(result, str)]
        self.url = next((result for result in successful_results if result), None)
        if not self.url:
            raise ConnectionError(
                f"Could not connect to Qdrant using any of the default hosts or the provided URL: {self.url}"
            )

        logger.info(f"Connection established using {self.url.split('@')[-1]}")

    async def _attempt_connection(self, url: str) -> str | None:
        """
        Attempts to connect to Qdrant at the given URL and returns the URL if successful.
        """
        client = None
        try:
            client = AsyncQdrantClient(url=url)
            await client.info()
            return url
        except Exception as e:
            logger.debug(f"Failed to connect to {url}: {e}")
            return None
        finally:
            if client:
                await client.close()


class Qdrant:
    def __init__(self, settings: Optional[QdrantSettings] = None):
        """
        Initializes the Qdrant client with specified settings.
        """
        self.settings = settings or QdrantSettings()
        self.retry_on: List[Type[Exception]] = []

    async def initialize(self, embedding_model: str, embedding_dims: int) -> None:
        """
        Initializes the Qdrant database, creating or updating a collection
        based on the embedding model and dimensions.
        """
        await self.settings.initialize()
        assert self.settings.url, "Missing settings.url"
        self.embedding_dims = embedding_dims
        self.embedding_model = embedding_model
        self.client = AsyncQdrantClient(self.settings.url)
        self.collection = encode_kv(self.embedding_model, str(self.embedding_dims))

        hnsw_on = models.HnswConfigDiff(
            m=0,
            payload_m=16,
            on_disk=self.settings.idx_on_disk,
        )
        hnsw_off = models.HnswConfigDiff(
            m=0,
            payload_m=0,
            on_disk=self.settings.idx_on_disk,
        )
        sparse_idx = models.SparseIndexParams(
            on_disk=self.settings.idx_on_disk,
            datatype=models.Datatype.UINT8,
        )

        index_configs = {
            NodeType.CHUNK: hnsw_on,
            NodeType.FACT: hnsw_off,
            NodeType.ENTITY: hnsw_on,
            EmbeddingType.SPARSE: sparse_idx,
        }

        multivector_on = models.MultiVectorConfig(
            comparator=models.MultiVectorComparator.MAX_SIM
        )
        multivector_configs = {
            NodeType.CHUNK: None,
            NodeType.FACT: multivector_on,
            NodeType.ENTITY: None,
        }

        exists = await self.client.collection_exists(collection_name=self.collection)
        if exists:
            collection_info = await self.client.get_collection(
                collection_name=self.collection
            )
            if collection_info.status == models.CollectionStatus.RED:
                raise ValueError(
                    f"Collection '{self.collection}' is in RED status. Please check and resolve the issue"
                )

            logger.info(
                f"Updating vector config in existing collection: '{self.collection}'."
            )
            await self.client.update_collection(
                collection_name=self.collection,
                vectors_config={
                    node_type.value: models.VectorParamsDiff(
                        hnsw_config=index_configs[node_type],
                        on_disk=self.settings.vec_on_disk,
                    )
                    for node_type in NodeType
                },
                sparse_vectors_config={
                    EmbeddingType.SPARSE.value: models.SparseVectorParams(
                        index=index_configs[EmbeddingType.SPARSE]
                    )
                },
            )

        else:
            logger.info(f"Creating new collection '{self.collection}'")
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config={
                    node_type.value: models.VectorParams(
                        size=self.embedding_dims,
                        distance=models.Distance.COSINE,
                        datatype=models.Datatype.FLOAT16,
                        on_disk=self.settings.vec_on_disk,
                        hnsw_config=index_configs[node_type],
                        multivector_config=multivector_configs[node_type]
                        if node_type in NodeType
                        else None,
                    )
                    for node_type in NodeType
                },
                sparse_vectors_config={
                    EmbeddingType.SPARSE.value: models.SparseVectorParams(
                        index=index_configs[EmbeddingType.SPARSE],
                        modifier=models.Modifier.IDF,
                    )
                },
            )

        await self.client.create_payload_index(
            collection_name=self.collection,
            field_name="search_space",
            field_schema=models.UuidIndexParams(
                type=models.UuidIndexType.UUID,
                is_tenant=True,
                on_disk=self.settings.idx_on_disk,
            ),
        )
        logger.info("Qdrant initialized successfully.")

    @retry()
    async def upsert_relation(
        self,
        relation: Relation,
        collection_name: Optional[str] = None,
        wait: bool = True,
    ) -> None:
        """
        Upserts a Relation object (chunk, facts, entities) as points into a Qdrant collection.
        """
        if not collection_name:
            collection_name = self.collection
        else:
            _ = decode_kv(collection_name)
        chunk = relation.chunk
        facts = relation.facts
        entities = relation.entities
        for n in entities:
            n.node_id = n.node_id or uuid.uuid4()

        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=str(cast(Id, chunk.node_id)),
                        payload=chunk.this_indexed_fields()
                        | {"content": chunk.content},
                        vector={
                            NodeType.CHUNK.value: cast(
                                List[float],
                                Embedding.get(
                                    chunk.embeddings, type=EmbeddingType.DENSE
                                )[0],
                            ),
                            NodeType.FACT.value: cast(
                                List[List[float]],
                                [
                                    Embedding.get(
                                        n.embeddings, type=EmbeddingType.DENSE
                                    )[0]
                                    for n in facts
                                ],
                            ),
                            EmbeddingType.SPARSE.value: Embedding.get(
                                chunk.embeddings, type=EmbeddingType.SPARSE
                            )[0].as_object(),
                        },
                    )
                ]
                + [
                    models.PointStruct(
                        id=str(cast(Id, n.node_id)),
                        payload={"search_space": n.search_space, "content": n.content},
                        vector={
                            NodeType.ENTITY.value: Embedding.get(
                                n.embeddings, type=EmbeddingType.DENSE
                            )[0]
                        },
                    )
                    for n in entities
                ],
                wait=wait,
            )

            logger.debug(
                f"Successfully upserted {3 + len(entities)} vectors into collection '{collection_name}'."
            )

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(
                    f"Qdrant upsert failed for collection '{collection_name}', nodes: {abbrev(relation)}."
                )
            raise

    @retry()
    @timeit(log_level=DEBUG, laps=1)
    async def get_points(
        self,
        query_points: List[QueryPoint],
        collection_name: Optional[str] = None,
        with_payload: bool | Sequence[str] = False,
    ) -> List[Point]:
        """
        Retrieves points from a Qdrant collection by their IDs.
        """
        if not query_points:
            return []
        if not collection_name:
            collection_name = self.collection
        else:
            _ = decode_kv(collection_name)

        results = await self.client.retrieve(
            collection_name=collection_name,
            ids=[q.node_id for q in query_points],
            with_payload=with_payload,
        )

        points = [Point(node_id=r.id, content=r.payload) for r in results]

        return points

    @retry()
    @timeit(log_level=DEBUG, laps=1)
    async def search_points(
        self,
        query_points: List[QueryPoint],
        search_space: uuid.UUID,
        threshold: float,
        limit: int = 30,
        oversampling: float = 2.0,
        collection_name: Optional[str] = None,
        explain: bool = False,
    ) -> List[QueryPoint]:
        """
        Finds matching points in Qdrant based on embedding similarity for a list of queries.
        Applies hybrid scoring if text_weight is provided.
        """
        if not query_points:
            return []
        if not collection_name:
            collection_name = self.collection
        else:
            _ = decode_kv(collection_name)

        try:
            filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="search_space",
                        match=models.MatchValue(value=str(search_space)),
                    ),
                ]
            )
            requests = []
            for q in query_points:
                embs = Embedding.get(embs=q.embeddings, type=EmbeddingType.DENSE)
                if bool(embs) == bool(q.node_id):
                    raise ValueError("Provide either embeddings or node_id")
                requests += [
                    models.QueryRequest(
                        query=q.node_id or embs[0],
                        filter=filter,
                        limit=max(
                            1, int(limit * oversampling) if q.text_weight else limit
                        ),
                        score_threshold=threshold,
                        using=q.node_type.value,
                        with_payload=["content"] if q.text_weight or explain else None,
                    )
                ]

            if not requests:
                return []

            batch_results = await self.client.query_batch_points(
                collection_name=collection_name,
                requests=requests,
            )

            for i, response in enumerate(batch_results):
                results = query_points[i].results = [
                    Point(
                        node_id=r.id,
                        similarity=r.score,
                        content=(r.payload or {}).get("content"),
                        query_content=query_points[i].content,
                    )
                    for r in response.points
                ]
                text_similarities = HybridScoring.get_fuzz_similarities(
                    query_points[i].content, results
                )
                for r in results:
                    adjusted_score = HybridScoring.ratio(
                        score=cast(float, r.similarity),
                        text_weight=query_points[i].text_weight,
                        text_similarity_scores=text_similarities,
                        response_id=r.node_id,
                    )
                    r.similarity = adjusted_score

                results = query_points[i].results = [
                    r for r in results if threshold <= cast(float, r.similarity)
                ]

                results.sort(key=lambda n: n.similarity or 0.0, reverse=True)
                results = query_points[i].results = results[:limit]

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(
                    f"Qdrant query failed for collection '{collection_name}', nodes: {abbrev(query_points)}."
                )
            raise

        flat_results = [
            {"p": r, "node_type": p.node_type.value}
            for p in query_points
            if p.results
            for r in p.results
        ]
        if not flat_results:
            logger.debug("Nothing found.")

        log_msg = f"Search space: {search_space}\nGraph entry points: {flat_results}"
        if explain:
            logger.info(log_msg)
        else:
            logger.debug(log_msg)

        return query_points

    @retry()
    @timeit(log_level=DEBUG, laps=1)
    async def search_relations(
        self,
        query: QueryPoint,
        search_space: uuid.UUID,
        threshold: float,
        limit: int = 10,
        oversampling: float = 2.0,
        collection_name: Optional[str] = None,
        explain: bool = False,
    ) -> List[Point]:
        """
        Finds related points (chunks and entities) in Qdrant based on a query point.
        Applies hybrid scoring and groups entity results.
        """
        if query.node_type != NodeType.CHUNK:
            raise ValueError("Only `chunk` type is allowed in this function.")
        if not collection_name:
            collection_name = self.collection
        else:
            _ = decode_kv(collection_name)

        sample_size = max(1, int(limit * oversampling))

        conditions: List[models.Condition] = [
            models.FieldCondition(
                key="search_space",
                match=models.MatchValue(value=str(search_space)),
            ),
        ]
        query_dense = Embedding.get(embs=query.embeddings, type=EmbeddingType.DENSE)[0]
        query_sparse = models.SparseVector(
            **Embedding.get(embs=query.embeddings, type=EmbeddingType.SPARSE)[
                0
            ].as_object()
        )
        filter = models.Filter(must=conditions)
        requests = [
            models.QueryRequest(
                prefetch=[
                    models.Prefetch(
                        prefetch=[
                            models.Prefetch(
                                query=query_dense,
                                filter=filter,
                                limit=sample_size * 2,
                                using=NodeType.CHUNK.value,
                            ),
                            models.Prefetch(
                                query=query_sparse,
                                using=EmbeddingType.SPARSE.value,
                                limit=sample_size * 2,
                            ),
                        ],
                        query=query_dense,
                        limit=sample_size * 2,
                        using=NodeType.FACT.value,
                    ),
                    models.Prefetch(
                        query=query_dense,
                        filter=filter,
                        limit=sample_size * 2,
                        using=NodeType.CHUNK.value,
                    ),
                    models.Prefetch(
                        query=query_sparse,
                        using=EmbeddingType.SPARSE.value,
                        limit=sample_size * 2,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.DBSF),
                limit=sample_size,
            ),
            models.QueryRequest(
                query=query_dense,
                filter=filter,
                limit=sample_size,
                using=NodeType.ENTITY.value,
                with_payload=["content"] if explain or query.text_weight else None,
            ),
        ]

        try:
            batch_results = await self.client.query_batch_points(
                collection_name=collection_name,
                requests=requests,
            )
            chunk_result, entity_result = batch_results[0], batch_results[1]

            entity_results = [
                Point(
                    node_id=p.id,
                    similarity=p.score,
                    content=(p.payload or {}).get("content"),
                    query_content=query.content,
                )
                for p in entity_result.points
            ]
            await self._group_points(
                points=entity_results,
                conditions=conditions,
                text_weight=query.text_weight,
                collection_name=collection_name,
            )

            chunk_results = [
                Point(
                    node_id=p.id,
                    similarity=p.score,
                    content=(p.payload or {}).get("content"),
                    query_content=query.content,
                )
                for p in chunk_result.points
            ]

            entity_text_similarities = HybridScoring.get_jaro_winkler_similarities(
                query.content, entity_results
            )
            rescale_similarity(entity_results)

            query.results = chunk_results + entity_results

            for r in query.results:
                if not r.similarity:
                    continue
                r.similarity = HybridScoring.ratio(
                    score=r.similarity,
                    text_weight=query.text_weight,
                    text_similarity_scores=entity_text_similarities,
                    response_id=r.node_id,
                )

            entity_results.sort(key=lambda n: n.similarity or 0.0, reverse=True)
            chunk_results.sort(key=lambda n: n.similarity or 0.0, reverse=True)
            query.results = entity_results[:limit] + chunk_results[:limit]

            rescale_similarity(entity_results, max_score=0.5)
            rescale_similarity(chunk_results, max_score=0.5)

            query.results = [
                r for r in query.results if r.similarity and threshold < r.similarity
            ]

        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(
                    f"Qdrant query failed for collection '{collection_name}', nodes: {abbrev(query)}."
                )
            raise

        if not query.results:
            logger.debug("Nothing found.")

        log_msg = f"Search space: {search_space}\nGraph entry points: {query.results}"
        if explain:
            logger.info(log_msg)
        else:
            logger.debug(log_msg)

        return query.results

    @retry()
    async def delete_points(
        self,
        point_ids: Sequence[uuid.UUID],
        collection_name: Optional[str] = None,
        flush_vectors: bool = True,
    ) -> Set[uuid.UUID]:
        """
        Deletes points from a Qdrant collection based on their IDs.
        Returns the IDs of the points that were targeted for deletion.
        """
        if not collection_name:
            collection_name = self.collection
        else:
            _ = decode_kv(collection_name)

        if not point_ids:
            logger.debug(
                f"No point IDs provided for deletion in collection '{collection_name}'. Skipping operation."
            )
            return set()

        point_ids_str = [str(p) for p in point_ids]
        deleted_point_ids: Set[uuid.UUID] = set()
        log_message_suffix = f"by IDs: {abbrev(point_ids)}"
        deleted_point_ids.update(point_ids)

        update_operations = [
            models.DeleteVectorsOperation(
                delete_vectors=models.DeleteVectors(
                    points=point_ids_str,
                    vector=[node_type.value for node_type in NodeType],
                )
            )
        ] + (
            [
                models.DeleteOperation(
                    delete=models.PointIdsList(points=point_ids_str)
                ),
            ]
            if flush_vectors
            else []
        )
        try:
            await self.client.batch_update_points(
                collection_name=collection_name, update_operations=update_operations
            )
            logger.debug(
                f"Successfully deleted points from collection '{collection_name}' {log_message_suffix}."
            )
        except Exception as e:
            if not any(isinstance(e, e_type) for e_type in self.retry_on):
                logger.exception(
                    f"Qdrant delete failed for collection '{collection_name}' {log_message_suffix}."
                )
            raise

        return deleted_point_ids

    async def _group_points(
        self,
        points: List[Point],
        conditions: List[models.Condition],
        text_weight: Optional[float],
        collection_name: Optional[str] = None,
        n_clusters: Optional[int] = None,
    ) -> None:
        """
        Groups a list of points into clusters based on their similarity,
        optionally incorporating text similarity.
        """
        if not collection_name:
            collection_name = self.collection
        else:
            _ = decode_kv(collection_name)

        cross_sim = await self.client.search_matrix_offsets(
            collection_name=collection_name,
            using=NodeType.ENTITY.value,
            sample=max(2, len(points)),
            limit=max(1, len(points)),
            query_filter=models.Filter(
                must=conditions
                + [models.HasIdCondition(has_id=[str(p.node_id) for p in points])]
            ),
        )

        offsets_row = np.array(cross_sim.offsets_row, dtype=np.int32)
        offsets_col = np.array(cross_sim.offsets_col, dtype=np.int32)
        scores = np.array(cross_sim.scores, dtype=np.float32)
        ids_str = np.array(cross_sim.ids, dtype=object)

        num_unique_ids = len(ids_str)

        if num_unique_ids == 0:
            for p in points:
                p.group_id = 0
            return

        if text_weight:
            id_to_point_map = {str(p.node_id): p for p in points}
            ordered_contents = [
                id_to_point_map[node_id].content or "" for node_id in ids_str
            ]

            jaro_winkler_similarities = np.array(
                [
                    distance.JaroWinkler.similarity(
                        ordered_contents[r], ordered_contents[c]
                    )
                    for r, c in zip(offsets_row, offsets_col)
                ],
                dtype=np.float32,
            )

            scores = (text_weight * jaro_winkler_similarities) + (
                (1 - text_weight) * scores
            )

        similarity_features = np.zeros(
            (num_unique_ids, num_unique_ids), dtype=np.float32
        )

        similarity_features[offsets_row, offsets_col] = scores
        similarity_features[offsets_col, offsets_row] = scores
        np.fill_diagonal(similarity_features, 1.0)

        n_clusters = n_clusters or int(math.sqrt(num_unique_ids))
        n_clusters = min(n_clusters, num_unique_ids)
        if n_clusters == 0:
            for p in points:
                p.group_id = 0
            return

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        cluster_labels = kmeans.fit_predict(similarity_features)
        group_ids = {
            node_id: int(cluster_labels[i]) for i, node_id in enumerate(ids_str)
        }

        for p in points:
            p.group_id = group_ids[str(p.node_id)]


def from_filters(filters: IndexedFilters) -> models.Filter:
    """
    Translates an `IndexedFilters` instance into a Qdrant `models.Filter` object.
    Supports EQ, IN, LT, LTE, GT, GTE operators for field conditions.
    """
    qdrant_field_conditions: List[models.FieldCondition] = []
    standardized_conditions = filters.std_conditions()

    for key, cond_list in standardized_conditions.items():
        current_range_params: Dict[str, float | str] = {}
        is_datetime_range_for_key = False

        for condition in cond_list:
            if condition.operator == Operator.EQ:
                qdrant_field_conditions.append(
                    models.FieldCondition(
                        key=key, match=models.MatchValue(value=condition.value)
                    )
                )
            elif condition.operator == Operator.IN:
                if not isinstance(condition.value, list):
                    raise ValueError(
                        f"Operator 'IN' for key '{key}' requires a list value, but got {type(condition.value).__name__}."
                    )
                qdrant_field_conditions.append(
                    models.FieldCondition(
                        key=key, match=models.MatchAny(any=condition.value)
                    )
                )
            elif condition.operator in (
                Operator.LT,
                Operator.LTE,
                Operator.GT,
                Operator.GTE,
            ):
                value = condition.value
                if not isinstance(value, (int, float, str)):
                    raise ValueError(
                        f"Range operator '{condition.operator.name}' for key '{key}' "
                        f"requires a numeric or string value, but got {type(value).__name__}."
                    )

                if isinstance(value, str):
                    if is_iso_datetime_string(value):
                        is_datetime_range_for_key = True
                    else:
                        raise ValueError(
                            f"String value '{value}' for range operator '{condition.operator.name}' "
                            f"on key '{key}' is not a valid ISO 8601 datetime string. "
                            f"Qdrant range filters require numeric or datetime strings."
                        )
                elif not isinstance(value, (int, float)):
                    raise ValueError(
                        f"Range operator '{condition.operator.name}' for key '{key}' "
                        f"requires a numeric value, but got {type(value).__name__}."
                    )

                if condition.operator == Operator.LT:
                    current_range_params["lt"] = value
                elif condition.operator == Operator.LTE:
                    current_range_params["lte"] = value
                elif condition.operator == Operator.GT:
                    current_range_params["gt"] = value
                elif condition.operator == Operator.GTE:
                    current_range_params["gte"] = value

        if current_range_params:
            if is_datetime_range_for_key:
                qdrant_field_conditions.append(
                    models.FieldCondition(
                        key=key, range=models.DatetimeRange(**current_range_params)
                    )
                )
            else:
                qdrant_field_conditions.append(
                    models.FieldCondition(
                        key=key, range=models.Range(**current_range_params)
                    )
                )

    return models.Filter(must=qdrant_field_conditions)


class HybridScoring:
    @staticmethod
    def get_fuzz_similarities(
        query_content: str, points: List[Point], max_score: float = 1.0
    ) -> Dict[Hashable, float]:
        """
        Calculates and normalizes text similarity ratios for points using `rapidfuzz.fuzz.ratio`.
        """
        raw_similarities: Dict[Hashable, float] = {
            p.node_id: fuzz.ratio(query_content, split_name_descriptor(p.content)[0])
            / 100.0
            for p in points
            if p.content
        }

        if not raw_similarities:
            return {}

        current_max_raw_score = max(raw_similarities.values())

        normalized_scores: Dict[Hashable, float] = {}
        if current_max_raw_score > 0:
            for node_id, score in raw_similarities.items():
                normalized_scores[node_id] = (score / current_max_raw_score) * max_score
        else:
            for node_id in raw_similarities.keys():
                normalized_scores[node_id] = 0.0

        return normalized_scores

    @staticmethod
    def get_jaro_winkler_similarities(
        query_content: str, points: List[Point], max_score: float = 1.0
    ) -> Dict[Hashable, float]:
        """
        Calculates and normalizes text similarity ratios for points using `rapidfuzz.distance.JaroWinkler.similarity`
        on individual words.
        """
        query_words = query_content.lower().split() if query_content else []

        if not query_words:
            return {p.node_id: 0.0 for p in points}

        raw_similarities: Dict[Hashable, float] = {}
        for p in points:
            if not p.content:
                raw_similarities[p.node_id] = 0.0
                continue

            point_name_parts = split_name_descriptor(p.content)[0].lower().split()

            max_similarity = 0.0
            max_similarity = max(
                (
                    distance.JaroWinkler.similarity(q_word, p_word)
                    for q_word in query_words
                    for p_word in point_name_parts
                ),
                default=0.0,
            )
            raw_similarities[p.node_id] = max_similarity

        if not raw_similarities:
            return {}

        current_max_raw_score = max(raw_similarities.values())

        if current_max_raw_score == 0:
            return {node_id: 0.0 for node_id in raw_similarities.keys()}

        normalized_scores: Dict[Hashable, float] = {}
        for node_id, score in raw_similarities.items():
            normalized_scores[node_id] = (score / current_max_raw_score) * max_score

        return normalized_scores

    @staticmethod
    def ratio(
        score: float,
        text_weight: Optional[float],
        text_similarity_scores: Dict[Hashable, float],
        response_id: uuid.UUID,
    ) -> float:
        """
        Calculates a hybrid score by combining vector similarity and text similarity
        based on a given `text_weight`.
        """
        if (
            text_weight
            and text_similarity_scores
            and response_id in text_similarity_scores
        ):
            vector_score = score * (1.0 - text_weight)
            text_score = text_similarity_scores[response_id]
            return vector_score + text_weight * text_score
        return score
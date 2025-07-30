import asyncio
import logging
import os
import uuid
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Set, Tuple

import aiofiles
import aiofiles.os as aio_os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# local imports
from ragchat.definitions import (
    ChatFilters,
    ChatMetadata,
    ChunkResult,
    Embedding,
    EmbeddingType,
    FileMetadata,
    FileState,
    FileStatus,
    Filters,
    Flow,
    IndexedFilters,
    IndexedMetadata,
    Language,
    Message,
    MessageClassification,
    Metadata,
    Node,
    NodeType,
    QueryPoint,
    Relation,
    SentinelFileState,
    encode_kv,
)
from ragchat.embedding import Embedder, EmbeddingSettings
from ragchat.llm import LLM, LlmSettings
from ragchat.log import abbrev, configure_logging, get_logger
from ragchat.neo4j import Neo4j, Neo4jSettings
from ragchat.parser import chunk_text, messages_to_user_text
from ragchat.progress import BatchProgress
from ragchat.prompts import RETRIEVAL_CHAT, RETRIEVAL_RAG
from ragchat.qdrant import Qdrant, QdrantSettings
from ragchat.utils import (
    NoContext,
    add_new_memories,
    remove_previous_memories,
)

logger = get_logger(__name__)
configure_logging()


class MemorySettings(BaseSettings):
    """
    Settings for memory operations.
    """

    chunk_char_size: int = 2000
    language: Language = Language.ENGLISH
    local_hosts: Optional[List[str]] = ["localhost", "host.docker.internal"]

    model_config = SettingsConfigDict(case_sensitive=False)

    @field_validator("local_hosts", mode="before")
    @classmethod
    def validate_hosts(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [m.strip() for m in v.split(",")]
        return v


logger.debug("testing")
logger.info("testing")
logger.warning("testing")
logger.error("testing")
logger.critical("testing")


class Memory:
    """
    Manages memory operations including upserting, searching, and recalling information
    using LLMs, embeddings, and a graph database.
    """

    def __init__(
        self,
        settings: Optional[MemorySettings] = None,
        llm_settings: Optional[LlmSettings] = None,
        embedder_settings: Optional[EmbeddingSettings] = None,
        neo4j_settings: Optional[Neo4jSettings] = None,
        qdrant_settings: Optional[QdrantSettings] = None,
    ):
        """
        Initializes the Memory instance with configuration settings and core components.

        Args:
            settings (Optional[MemorySettings]): Configuration settings. Defaults to MemorySettings().
            llm_settings (Optional[LlmSettings]): Settings for the LLM.
            embedder_settings (Optional[EmbeddingSettings]): Settings for the embedder.
            neo4j_settings (Optional[Neo4jSettings]): Settings for Neo4j.
            qdrant_settings (Optional[QdrantSettings]): Settings for Qdrant.
        """
        self.settings = settings or MemorySettings()
        self.llm = LLM(llm_settings)
        self.embedder = Embedder(embedder_settings)
        self.neo4j = Neo4j(neo4j_settings)
        self.qdrant = Qdrant(qdrant_settings)

        # Dictionary to track ongoing file processing tasks for cancellation
        self._processing_tasks: Dict[str, asyncio.Task[Any]] = {}

    async def initialize(self) -> None:
        """
        Initializes the underlying graph database, LLM, and embedder components.
        """
        await asyncio.gather(
            self.embedder.initialize(),
            self.neo4j.initialize(),
            self.llm.initialize(),
        )
        assert self.embedder.settings.model
        assert self.embedder.settings.dims
        await self.qdrant.initialize(
            self.embedder.settings.model, self.embedder.settings.dims
        )

    async def upsert(
        self,
        text: str,
        metadata: Metadata,
        db_sem: Optional[asyncio.Semaphore] = None,
        context: Optional[str] = None,
        flow: Optional[Flow] = None,
        language: Optional[Language] = None,
        replace_threshold: float = 0.9,
        text_weight: float = 0.5,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        emb_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Optional[Relation]:
        """
        Extracts a relation from text, embeds it, and upserts it into the graph and vector database.

        Args:
            text (str): The text to process.
            metadata (Metadata): Metadata associated with the text.
            db_sem (Optional[asyncio.Semaphore]): Semaphore for database concurrency control.
            context (Optional[str]): Additional context for the LLM.
            flow (Optional[Flow]): The flow associated with the text.
            language (Optional[Language]): Language for processing.
            replace_threshold (float): Similarity threshold for replacing existing nodes.
            text_weight (float): Weight for text similarity in search.
            llm_kwargs (Optional[Dict[str, Any]]): Arguments for the LLM.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder.

        Returns:
            Optional[Relation]: The relation successfully upserted into the graph, or None if no relation was extracted.
        """
        language = language or self.settings.language
        llm_kwargs = llm_kwargs or {}
        emb_kwargs = emb_kwargs or {}
        context_manager = db_sem or NoContext()
        indexed_metadata = IndexedMetadata(metadata=metadata)
        flow = flow or indexed_metadata.flow

        try:
            relation = await self.llm.extract_relation(
                text=text,
                indexed_metadata=indexed_metadata,
                context=context,
                flow=flow,
                language=language,
                **llm_kwargs,
            )
            if not relation:
                logger.debug("No relation extracted.")
                return None

            await self.embedder.embed_relations([relation], **emb_kwargs)

            collection_name: Optional[str] = None
            if emb_kwargs:
                emb_model = str(emb_kwargs.get("model", ""))
                emb_dims = str(int(emb_kwargs.get("dims", 0)))
                collection_name = encode_kv(emb_model, emb_dims)

            node_ids: Dict[uuid.UUID, uuid.UUID] = {}
            entities = [n for n in relation.to_list(include=[NodeType.ENTITY])]
            for e in entities:
                e.node_id = node_ids.get(e._hash, e.node_id)
            new_entities = [e for e in entities if not e.node_id]

            async with context_manager:
                if new_entities:
                    query_points = [
                        QueryPoint(
                            embeddings=e.embeddings,
                            node_type=e.node_type,
                            content=e.content,
                            text_weight=text_weight,
                        )
                        for e in new_entities
                    ]
                    await self.qdrant.search_points(
                        query_points=query_points,
                        search_space=relation.chunk.search_space,
                        threshold=replace_threshold,
                        limit=1,
                        oversampling=3.0,
                        collection_name=collection_name,
                    )
                    for j, q in enumerate(query_points):
                        if not q.results:
                            continue
                        e = new_entities[j]
                        e.node_id = q.results[0].node_id
                        assert e.node_id, "Missing node_id"
                        node_ids[e._hash] = e.node_id

                await self.qdrant.upsert_relation(relation, collection_name)
                await self.neo4j.upsert_relation(relation)

            logger.debug(
                "Upserted 1 relation"
                + (f": {abbrev(relation)}" if logger.level <= logging.DEBUG else "")
            )

        except Exception as e:
            logger.exception(f"Error adding memory: {e}")
            raise
        return relation

    async def cancel_file_upsert(self, task_id: str) -> bool:
        """
        Cancels a running file upsert task by its ID.

        Args:
            task_id (str): The ID of the task to cancel.

        Returns:
            bool: True if cancellation was requested, False if task not found or finished.
        """
        task = self._processing_tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancellation requested for task ID: {task_id}")
            return True
        logger.warning(f"Task ID not found or already finished: {task_id}")
        return False

    async def file_upsert(
        self,
        metadata: FileMetadata,
        db_sem: asyncio.Semaphore,
        context: Optional[str] = None,
        flow: Optional[Flow] = None,
        language: Optional[Language] = None,
        replace_threshold: float = 0.9,
        text_weight: float = 0.5,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        emb_kwargs: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[FileState]:
        """
        Processes a single file by chunking its content, extracting relations,
        and upserting them into the graph and vector database.
        Yields FileState updates to report progress and status.

        Args:
            metadata (FileMetadata): Metadata for the file.
            db_sem (asyncio.Semaphore): Semaphore for database concurrency control.
            context (Optional[str]): Additional context for the LLM.
            flow (Optional[Flow]): The flow associated with the file.
            language (Optional[Language]): Language for processing.
            replace_threshold (float): Similarity threshold for replacing existing nodes.
            text_weight (float): Weight for text similarity in search.
            llm_kwargs (Optional[Dict[str, Any]]): Arguments for the LLM.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder.

        Yields:
            AsyncIterator[FileState]: Updates on the file processing status.
        """
        file_path = metadata.path
        file_name = os.path.basename(file_path)
        task_id = f"file_upsert_{file_name}_{uuid.uuid4()}"
        current_task = asyncio.current_task()
        if current_task:
            self._processing_tasks[task_id] = current_task

        file_state = FileState(
            file_path=file_path, task_id=task_id, status=FileStatus.PENDING
        )
        yield file_state

        file_text = ""
        current_file_total_bytes = 0.0
        current_file_processed_bytes = 0.0

        try:
            if not metadata.folder_id:
                raise ValueError(f"Missing metadata.folder_id for {file_name}")
            if not metadata.file_id:
                metadata.file_id = file_name

            language = language or self.settings.language
            llm_kwargs = llm_kwargs or {}
            emb_kwargs = emb_kwargs or {}

            try:
                async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
                    file_text = await f.read()
                current_file_total_bytes = float(len(file_text.encode("utf-8")))
                file_state.total_bytes = current_file_total_bytes
                yield file_state
            except FileNotFoundError:
                yield FileState.create_error_state(
                    file_path, f"File not found: {file_path}", task_id
                )
                return
            except Exception as e:
                yield FileState.create_error_state(
                    file_path, f"Error reading file {file_path}: {e}", task_id
                )
                return

            chunks = chunk_text(
                file_text, chunk_char_size=self.settings.chunk_char_size
            )
            if not chunks:
                file_state.total_chunks = 0
                file_state.status = FileStatus.COMPLETED
                file_state.processed_bytes = current_file_total_bytes
                yield file_state
                return

            context = context or f"Source: {file_name}"
            total_chunks = len(chunks)
            file_state.total_chunks = total_chunks

            for i, chunk_content in enumerate(chunks):
                if current_task and current_task.cancelled():
                    file_state.status = FileStatus.CANCELLED
                    file_state.error = "Processing cancelled."
                    yield file_state
                    return

                if file_state.status == FileStatus.PENDING:
                    file_state.status = FileStatus.PROCESSING
                    yield file_state

                chunk_result = ChunkResult(chunk_index=i)
                try:
                    m = metadata.model_dump(exclude_none=True) | {
                        "ichunk": i,
                        "chunks": total_chunks,
                    }
                    upserted = await self.upsert(
                        text=chunk_content,
                        metadata=FileMetadata(**m),
                        db_sem=db_sem,
                        context=context,
                        flow=flow,
                        language=language,
                        replace_threshold=replace_threshold,
                        text_weight=text_weight,
                        llm_kwargs=llm_kwargs,
                        emb_kwargs=emb_kwargs,
                    )
                    chunk_result.id = upserted.chunk.node_id if upserted else None

                    current_file_processed_bytes += float(
                        len(chunk_content.encode("utf-8"))
                    )
                    file_state.processed_bytes = current_file_processed_bytes
                    file_state.update_with_chunk_result(chunk_result)
                    yield file_state
                except asyncio.CancelledError:
                    file_state.status = FileStatus.CANCELLED
                    file_state.error = "Chunk processing cancelled."
                    yield file_state
                    raise
                except Exception as e:
                    logger.error(
                        f"Error processing chunk {i} for file {file_name}: {e}",
                        exc_info=True,
                    )
                    chunk_result.error = str(e)
                    file_state.update_with_chunk_result(chunk_result)
                    yield file_state

        except asyncio.CancelledError:
            if not file_state.is_terminal:
                file_state.status = FileStatus.CANCELLED
                file_state.error = "Processing cancelled."
                yield file_state
            raise
        except Exception as e:
            logger.error(f"Error in file_upsert for {file_name}: {e}", exc_info=True)
            if not file_state.is_terminal:
                file_state.status = FileStatus.ERROR
                file_state.error = str(e)
                yield file_state
        finally:
            if task_id in self._processing_tasks:
                del self._processing_tasks[task_id]

    async def file_upsert_batch(
        self,
        metadatas: List[FileMetadata],
        context: Optional[str] = None,
        flow: Optional[Flow] = None,
        language: Optional[Language] = None,
        replace_threshold: float = 0.9,
        text_weight: float = 0.5,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        emb_kwargs: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[FileState]:
        """
        Processes a batch of files concurrently, yielding FileState updates for each file.

        Args:
            metadatas (List[FileMetadata]): A list of metadata for files to process.
            context (Optional[str]): Additional context for the LLM.
            flow (Optional[Flow]): The flow associated with the files.
            language (Optional[Language]): Language for processing.
            replace_threshold (float): Similarity threshold for replacing existing nodes.
            text_weight (float): Weight for text similarity in search.
            llm_kwargs (Optional[Dict[str, Any]]): Arguments for the LLM.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder.

        Yields:
            AsyncIterator[FileState]: Updates on the processing status of individual files in the batch.
        """
        total_files = len(metadatas)
        if total_files == 0:
            return

        results_queue: asyncio.Queue[FileState] = asyncio.Queue()
        sentinel = SentinelFileState()
        db_sem = asyncio.Semaphore()

        async def run_single_file_producer(
            sem: asyncio.Semaphore,
            db_sem: asyncio.Semaphore,
            metadata_item: FileMetadata,
            q: asyncio.Queue[FileState],
            common_kwargs: Any,
        ) -> None:
            file_path = metadata_item.path
            file_name = os.path.basename(file_path)
            task_id_for_error: Optional[str] = (
                f"file_upsert_{file_name}_init_error_{uuid.uuid4()}"
            )
            first_result_yielded = False
            await sem.acquire()
            try:
                async for state in self.file_upsert(
                    metadata=metadata_item, db_sem=db_sem, **common_kwargs
                ):
                    if not first_result_yielded and state.task_id:
                        task_id_for_error = state.task_id
                        first_result_yielded = True
                    await q.put(state)
            except asyncio.CancelledError:
                await q.put(
                    FileState(
                        file_path=file_path,
                        task_id=task_id_for_error,
                        status=FileStatus.CANCELLED,
                        error="Processing cancelled.",
                    )
                )
                raise
            except Exception as e:
                logger.error(f"Producer error for {file_name}: {e}", exc_info=True)
                await q.put(
                    FileState.create_error_state(
                        file_path, f"Producer error: {e}", task_id=task_id_for_error
                    )
                )
                raise
            finally:
                sem.release()
                await q.put(sentinel)

        producer_tasks: List[asyncio.Task[None]] = []
        common_kwargs = {
            "context": context,
            "flow": flow,
            "language": language,
            "replace_threshold": replace_threshold,
            "text_weight": text_weight,
            "llm_kwargs": llm_kwargs,
            "emb_kwargs": emb_kwargs,
        }

        for metadata_item in metadatas:
            producer_tasks.append(
                asyncio.create_task(
                    run_single_file_producer(
                        sem=self.llm.semaphore,
                        db_sem=db_sem,
                        metadata_item=metadata_item,
                        q=results_queue,
                        common_kwargs=common_kwargs,
                    )
                )
            )

        completed_producers = 0
        try:
            while completed_producers < total_files:
                result = await results_queue.get()
                if result is sentinel:
                    completed_producers += 1
                elif isinstance(result, FileState):
                    yield result
                results_queue.task_done()
        except asyncio.CancelledError:
            for task in producer_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*producer_tasks, return_exceptions=True)
            raise
        except Exception as e:
            logger.error(f"Error consuming from results queue: {e}", exc_info=True)
            for task in producer_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*producer_tasks, return_exceptions=True)
            raise
        finally:
            if any(not task.done() for task in producer_tasks):
                await asyncio.gather(*producer_tasks, return_exceptions=True)

    async def stream_file_upsert_batch(
        self,
        metadatas: List[FileMetadata],
        context: Optional[str] = None,
        flow: Optional[Flow] = None,
        language: Optional[Language] = None,
        replace_threshold: float = 0.9,
        text_weight: float = 0.5,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        emb_kwargs: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Streams progress updates as a batch of files is processed and upserted.

        Args:
            metadatas (List[FileMetadata]): A list of metadata for files to process.
            context (Optional[str]): Additional context for the LLM.
            flow (Optional[Flow]): The flow associated with the files.
            language (Optional[Language]): Language for processing.
            replace_threshold (float): Similarity threshold for replacing existing nodes.
            text_weight (float): Weight for text similarity in search.
            llm_kwargs (Optional[Dict[str, Any]]): Arguments for the LLM.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder.

        Yields:
            AsyncIterator[str]: JSON string representations of BatchProgress updates.
        """
        total_files = len(metadatas)
        total_batch_bytes_expected = 0.0

        if total_files > 0:
            stat_tasks = []
            for metadata_item in metadatas:

                async def get_size(path_to_stat: str) -> float:
                    try:
                        stat_result = await aio_os.stat(path_to_stat)
                        return float(stat_result.st_size)
                    except FileNotFoundError:
                        logger.warning(
                            f"File not found for size calc: {path_to_stat}. Treating as 0 bytes."
                        )
                        return 0.0
                    except Exception as e:
                        logger.error(
                            f"Error getting size for {path_to_stat}: {e}. Treating as 0 bytes."
                        )
                        return 0.0

                stat_tasks.append(get_size(metadata_item.path))

            file_sizes = await asyncio.gather(*stat_tasks)
            total_batch_bytes_expected = sum(s for s in file_sizes if s is not None)

        progress = BatchProgress(
            total_files=total_files,
            total_batch_bytes_expected=total_batch_bytes_expected,
        )
        logger.info(
            f"Starting streamed batch for {total_files} files, total expected size: {progress.format_bytes(total_batch_bytes_expected)}."
        )

        update = await progress.maybe_get_progress_update(with_files=True)
        if update:
            yield update

        if total_files == 0:
            logger.info("Streamed batch file upsert generator finished (no files).")
            return

        try:
            async for file_state in self.file_upsert_batch(
                metadatas=metadatas,
                context=context,
                flow=flow,
                language=language,
                replace_threshold=replace_threshold,
                text_weight=text_weight,
                llm_kwargs=llm_kwargs,
                emb_kwargs=emb_kwargs,
            ):
                await progress.handle_file_state(file_state)
                update = await progress.maybe_get_progress_update(with_files=False)
                if update:
                    yield update

            update = await progress.maybe_get_progress_update(with_files=True)
            if update:
                yield update

        except asyncio.CancelledError:
            logger.warning("Batch processing cancelled.")
            non_terminal_task_ids = await progress.get_non_terminal_task_ids()
            for task_id in non_terminal_task_ids:
                current_state = progress.file_states.get(task_id)
                if current_state:
                    await progress.handle_file_state(
                        FileState.create_cancelled_state(
                            current_state.file_path, task_id=task_id
                        )
                    )
            update = await progress.maybe_get_progress_update(with_files=True)
            if update:
                yield update
            raise
        except Exception as e:
            logger.exception("Error during batch processing stream.")
            non_terminal_task_ids = await progress.get_non_terminal_task_ids()
            error_msg = str(e)
            for task_id in non_terminal_task_ids:
                current_state = progress.file_states.get(task_id)
                if current_state:
                    await progress.handle_file_state(
                        FileState.create_error_state(
                            current_state.file_path, error_msg, task_id=task_id
                        )
                    )
            update = await progress.maybe_get_progress_update(with_files=True)
            if update:
                yield update
            raise
        finally:
            logger.info("Streamed batch file upsert generator finished.")

    async def search_chunks(
        self,
        query: str,
        filters: Filters,
        context: Optional[str] = None,
        text_weight: float = 0.5,
        threshold: float = 0.0,
        retry_threshold: float = 0.0,
        limit: int = 5,
        char_limit: int = 12000,
        oversampling: float = 2.0,
        max_hops: int = 3,
        explain: bool = False,
        profile: bool = False,
        language: Optional[Language] = None,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        emb_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[Node]:
        """
        Searches for relevant chunk nodes in the graph database based on a query and filters.

        Args:
            query (str): The search query string.
            filters (Filters): Filter criteria to apply to the search.
            context (Optional[str]): Additional context for the search.
            text_weight (float): Weight for text similarity in search.
            threshold (float): The similarity threshold for initial search.
            retry_threshold (float): A lower threshold to use if the initial search yields no results.
            limit (int): The maximum number of results to return.
            char_limit (int): The maximum total character length of the returned chunk content.
            oversampling (float): Factor to oversample results from vector DB before graph filtering.
            max_hops (int): Maximum number of hops for graph traversal during search.
            explain (bool): If True, includes explanation details in the results.
            profile (bool): If True, profiles the search query (for Neo4j).
            language (Optional[Language]): Language for processing.
            llm_kwargs (Optional[Dict[str, Any]]): Arguments for the LLM.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder.

        Returns:
            List[Node]: A list of relevant chunk nodes found.
        """
        if not query:
            return []
        if not filters:
            raise ValueError("Missing filters.")
        indexed_filters = IndexedFilters(filters=filters)
        language = language or self.settings.language
        llm_kwargs = llm_kwargs or {}
        emb_kwargs = emb_kwargs or {}

        embeddings = [
            Embedding(
                type=EmbeddingType.SPARSE,
                vec=list(self.embedder.bm25.embed([query]))[0],
            ),
            Embedding(
                type=EmbeddingType.DENSE,
                vec=(await self.embedder.embed([query], **emb_kwargs))[0],
            ),
        ]
        query_point = QueryPoint(
            content=query,
            embeddings=embeddings,
            node_type=NodeType.CHUNK,
            text_weight=text_weight,
        )

        if emb_kwargs:
            emb_model = str(emb_kwargs.get("model", ""))
            emb_dims = str(int(emb_kwargs.get("dims", 0)))
            collection_name = encode_kv(emb_model, emb_dims)
        else:
            collection_name = None

        points = await self.qdrant.search_relations(
            query=query_point,
            search_space=indexed_filters.search_space,
            threshold=threshold,
            limit=max(1, int(limit * oversampling)),
            oversampling=oversampling,
            collection_name=collection_name,
            explain=explain,
        )
        relevant_nodes: List[Node] = await self.neo4j.search_chunks_from_points(
            points=points,
            indexed_filters=indexed_filters,
            threshold=threshold,
            limit=limit,
            char_limit=char_limit,
            max_hops=max_hops,
            explain=explain,
            profile=profile,
        )
        if not relevant_nodes and threshold < retry_threshold:
            logger.debug(
                f"No relevant chunks found. Retrying with a lower threshold ({retry_threshold})..."
            )
            points = await self.qdrant.search_relations(
                query=query_point,
                search_space=indexed_filters.search_space,
                threshold=retry_threshold,
                limit=max(1, int(limit * oversampling)),
                oversampling=oversampling,
                collection_name=collection_name,
                explain=explain,
            )
            relevant_nodes = await self.neo4j.search_chunks_from_points(
                points=points,
                indexed_filters=indexed_filters,
                threshold=retry_threshold,
                limit=limit,
                char_limit=char_limit,
                max_hops=max_hops,
                explain=explain,
                profile=profile,
            )

        return relevant_nodes

    async def update_nodes(
        self,
        nodes: List[Node],
        return_fields: Optional[set[str]] = None,
        emb_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[Node]:
        """
        Updates multiple nodes by their IDs in the graph database.
        Existing properties are preserved when new values are null. Embeddings are
        re-calculated if the node content changes.

        Args:
            nodes (List[Node]): A list of Node objects to update. Must include node_id.
            return_fields (Optional[set[str]]): Specific fields to return for each updated node.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder.

        Returns:
            List[Node]: The updated Node objects as retrieved from the database.
        """
        emb_kwargs = emb_kwargs or {}
        if not nodes:
            return []
        await self.embedder.embed_nodes(nodes, **emb_kwargs)
        await self.neo4j.update_nodes_by_ids(nodes, return_fields)

        return nodes

    async def recall(
        self,
        messages: List[Message],
        filters: Filters,
        context: Optional[str] = None,
        flow: Optional[Flow] = None,
        text_weight: float = 0.5,
        threshold: float = 0.0,
        retry_threshold: float = 0.0,
        fallback: Optional[Literal["first", "last"]] = None,
        limit: int = 5,
        char_limit: int = 12000,
        oversampling: float = 2.0,
        max_hops: int = 3,
        explain: bool = False,
        profile: bool = False,
        language: Optional[Language] = None,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        emb_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Message], List[Node]]:
        """
        Retrieves relevant memories (chunks) based on the user's query within the messages
        and adds them to the messages list, typically modifying the system prompt or user message.

        Args:
            messages (List[Message]): The list of messages, including the user's query.
            filters (Filters): Filter criteria to apply when searching for memories.
            context (Optional[str]): Additional context for the LLM during query relation extraction.
            flow (Optional[Flow]): The flow associated with the messages.
            text_weight (float): Weight for text similarity in search.
            threshold (float): The similarity threshold for initial search.
            retry_threshold (float): A lower threshold to use if the initial search yields no results.
            fallback (Optional[Literal["first", "last"]]): If no results are found via search, fall back to retrieving the 'first' or 'last' few nodes based on creation/update time.
            limit (int): The maximum number of relevant chunks to retrieve via search.
            char_limit (int): The maximum total character length of the returned chunk content from search.
            oversampling (float): Factor to oversample results from vector DB before graph filtering.
            max_hops (int): Maximum number of hops for graph traversal during search.
            explain (bool): If True, includes explanation details in search results.
            profile (bool): If True, profiles the search query (for Neo4j).
            language (Optional[Language]): Language for processing.
            llm_kwargs (Optional[Dict[str, Any]]): Arguments for the LLM.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder.

        Returns:
            Tuple[List[Message], List[Node]]: A tuple containing the updated list of messages
                                              (with memories added) and the list of relevant
                                              Node objects that were retrieved.
        """
        if not messages:
            return [], []
        if not filters:
            raise ValueError("Missing filters.")
        if fallback not in ["first", "last", None]:
            raise ValueError("Invalid fallback value.")
        indexed_filters = IndexedFilters(filters=filters)
        flow = flow or indexed_filters.flow
        language = language or self.settings.language
        llm_kwargs = llm_kwargs or {}

        remove_previous_memories(messages, flow)

        if messages and messages[0].role != "system":
            if flow == Flow.FILE:
                prompt = RETRIEVAL_RAG.to_str(flow, language)
            elif flow == Flow.CHAT:
                prompt = RETRIEVAL_CHAT.to_str(flow, language)
            else:
                prompt = ""
                logger.warning(f"No specific RAG prompt for flow: {flow}")

            if prompt:
                messages.insert(0, Message(role="system", content=prompt))

        query: str = messages_to_user_text(messages)
        nodes = await self.search_chunks(
            query=query,
            filters=filters,
            context=context,
            text_weight=text_weight,
            threshold=threshold,
            retry_threshold=retry_threshold,
            limit=limit,
            char_limit=char_limit,
            oversampling=oversampling,
            max_hops=max_hops,
            explain=explain,
            profile=profile,
            language=language,
            llm_kwargs=llm_kwargs,
            emb_kwargs=emb_kwargs,
        )

        if not nodes and fallback:
            logger.info(
                f"Nothing found from similarity search, falling back to: {fallback}, from filters: {filters}"
            )
            nodes = await self.neo4j.get_nodes(
                indexed_filters=indexed_filters,
                order_by="created_at" if fallback == "first" else "updated_at",
                order_direction="asc" if fallback == "first" else "desc",
                limit=3,
            )

        add_new_memories(messages, nodes, flow)

        return messages, nodes

    async def chat(
        self,
        messages: List[Message],
        metadata: ChatMetadata,
        filters: ChatFilters,
        context: Optional[str] = None,
        threshold: float = 0.0,
        retry_threshold: float = 0.0,
        replace_threshold: float = 0.9,
        limit: int = 5,
        char_limit: int = 12000,
        oversampling: float = 2.0,
        max_hops: int = 3,
        explain: bool = False,
        profile: bool = False,
        language: Optional[Language] = None,
        llm_kwargs: Optional[Dict[str, Any]] = None,
        emb_kwargs: Optional[Dict[str, Any]] = None,
        sequential_upsert: bool = False,
    ) -> List[Message]:
        """
        Performs a chat interaction by recalling relevant memories based on the message history
        and filters, adding them to the messages, and optionally upserting the latest message
        as a new memory if classified as a statement.

        Args:
            messages (List[Message]): The list of messages in the conversation history.
            metadata (ChatMetadata): Metadata associated with the chat session.
            filters (ChatFilters): Filter criteria to apply when searching for memories. Must include user_id.
            context (Optional[str]): Additional context for the LLM during recall and upsert.
            threshold (float): The similarity threshold for initial search during recall.
            retry_threshold (float): A lower threshold for search retry during recall.
            replace_threshold (float): Similarity threshold for replacing existing nodes during upsert.
            limit (int): The maximum number of relevant chunks to retrieve during recall.
            char_limit (int): The maximum total character length of recalled chunks.
            oversampling (float): Factor to oversample results from vector DB before graph filtering.
            max_hops (int): Maximum number of hops for graph traversal during search.
            explain (bool): If True, includes explanation details in recall search results.
            profile (bool): If True, profiles the search query (for Neo4j).
            language (Optional[Language]): Language for processing.
            llm_kwargs (Optional[Dict[str, Any]]): Arguments for the LLM.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder.
            sequential_upsert (bool): If True, the upsert operation (if triggered) will be awaited
                                      before returning. If False, it will be scheduled as a background task.

        Returns:
            List[Message]: The updated list of messages with recalled memories added.
        """
        if not messages:
            return []
        if not filters:
            raise ValueError("Missing filters.")
        if not filters.user_id:
            raise ValueError("Missing filters.user_id")

        language = language or self.settings.language
        llm_kwargs = llm_kwargs or {}
        emb_kwargs = emb_kwargs or {}

        text = messages_to_user_text(messages)

        await self.recall(
            messages=messages,
            filters=filters,
            context=context,
            threshold=threshold,
            retry_threshold=retry_threshold,
            limit=limit,
            char_limit=char_limit,
            oversampling=oversampling,
            max_hops=max_hops,
            explain=explain,
            profile=profile,
            language=language,
            llm_kwargs=llm_kwargs,
            emb_kwargs=emb_kwargs,
        )

        async def classify_and_upsert(
            messages: List[Message],
            metadata: Metadata,
            context: Optional[str],
            language: Language,
            llm_kwargs: Any,
        ) -> None:
            msg_type = await self.llm.classify_message(
                text, context, Flow.CHAT, language, **llm_kwargs
            )
            if msg_type != MessageClassification.STATEMENT:
                return

            await self.upsert(
                text=messages_to_user_text(messages),
                metadata=metadata,
                context=context,
                language=language,
                replace_threshold=replace_threshold,
                llm_kwargs=llm_kwargs,
                emb_kwargs=emb_kwargs,
            )

        if sequential_upsert:
            await classify_and_upsert(messages, metadata, context, language, llm_kwargs)
        else:
            asyncio.create_task(
                classify_and_upsert(messages, metadata, context, language, llm_kwargs)
            )

        return messages

    async def get_updated_at(
        self,
        filters: Filters,
        return_fields: Optional[set[str]] = None,
        order_by: Optional[str] = "updated_at",
        order_direction: Optional[str] = "desc",
        limit: Optional[int] = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the latest 'updated_at' timestamp and optionally other fields
        for nodes matching the filters, grouped by the specified return_fields.

        Args:
            filters (Filters): Filter criteria to apply to the query.
            return_fields (Optional[set[str]]): Fields to group by and return along with the latest updated_at.
            order_by (Optional[str]): Property to order results by.
            order_direction (Optional[str]): Direction of ordering, "asc" or "desc".
            limit (Optional[int]): Maximum number of results to return.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the requested
                                  return_fields and the latest 'updated_at' for that group.
        """
        if not filters:
            raise ValueError("Missing filters.")
        indexed_filters = IndexedFilters(filters=filters)
        results = await self.neo4j.get_updated_at(
            indexed_filters=indexed_filters,
            return_fields=return_fields,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

        return results

    async def get_nodes_by_ids(
        self,
        node_ids: List[str],
        node_type: NodeType = NodeType.CHUNK,
        return_fields: Optional[set[str]] = None,
    ) -> List[Node]:
        """
        Retrieves multiple nodes by their unique IDs from the graph database.

        Args:
            node_ids (List[str]): A list of node IDs to retrieve.
            node_type (NodeType): The type of node to retrieve.
            return_fields (Optional[set[str]]): Specific fields to return for each node.

        Returns:
            List[Node]: A list of the retrieved Node objects. Returns an empty list if no nodes are found or node_ids is empty.
        """
        if not node_ids:
            return []

        nodes = await self.neo4j.get_nodes_by_ids(
            node_ids=node_ids,
            node_type=node_type,
            return_fields=return_fields,
        )

        return nodes

    async def get_nodes(
        self,
        filters: Filters,
        node_type: NodeType = NodeType.CHUNK,
        return_fields: Optional[set[str]] = None,
        order_by: str = "updated_at",
        order_direction: str = "desc",
        limit: int = 100,
    ) -> List[Node]:
        """
        Retrieves nodes from the graph database based on filters, with optional ordering and limiting.

        Args:
            filters (Filters): Filter criteria to apply to the query (required).
            node_type (NodeType): The type of node to retrieve.
            return_fields (Optional[set[str]]): Specific fields to return for each node.
            order_by (str): Property to order results by.
            order_direction (str): Direction of ordering, "asc" or "desc".
            limit (int): Maximum number of nodes to return.

        Returns:
            List[Node]: A list of the retrieved Node objects. Returns an empty list if no nodes are found or filters are empty.
        """
        if not filters:
            raise ValueError("Missing filters.")
        indexed_filters = IndexedFilters(filters=filters)

        nodes = await self.neo4j.get_nodes(
            indexed_filters=indexed_filters,
            node_type=node_type,
            return_fields=return_fields,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

        return nodes

    async def delete_nodes(
        self,
        node_ids: Optional[List[str]] = None,
        filters: Optional[Filters] = None,
        node_type: NodeType = NodeType.CHUNK,
        return_fields: Optional[Set[str]] = None,
        cleanup: bool = True,
        emb_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[Node]:
        """
        Deletes nodes from the graph database either by a list of unique IDs or by filter criteria.
        Also deletes corresponding points from the vector database.

        Args:
            node_ids (Optional[List[str]]): A list of node IDs to delete.
            filters (Optional[Filters]): Filter criteria to apply to the query.
            node_type (NodeType): The type of node to delete.
            return_fields (Set[str]): Specific fields of the deleted nodes to return.
            cleanup (bool): If True, performs cleanup operations for orphaned nodes/relations after deletion.
            emb_kwargs (Optional[Dict[str, Any]]): Arguments for the embedder, used to determine Qdrant collection.

        Returns:
            List[Node]: A list of the deleted Node objects. Returns an empty list if no nodes are found.

        Raises:
            ValueError: If neither node_ids nor filters are provided, or if both are provided.
        """
        if (not node_ids) == (not filters):
            raise ValueError("Exactly one of 'node_ids' or 'filters' must be provided.")

        if emb_kwargs:
            emb_model = str(emb_kwargs.get("model", ""))
            emb_dims = str(int(emb_kwargs.get("dims", 0)))
            collection_name = encode_kv(emb_model, emb_dims)
        else:
            collection_name = None

        deleted_nodes: List[Node]

        if node_ids:
            deleted_nodes = await self.neo4j.delete_nodes_by_ids(
                node_ids=node_ids,
                node_type=node_type,
                return_fields=return_fields,
                cleanup=cleanup,
            )
        else:
            indexed_filters = IndexedFilters(filters=filters)
            deleted_nodes = await self.neo4j.delete_nodes(
                indexed_filters=indexed_filters,
                node_type=node_type,
                return_fields=return_fields,
                cleanup=cleanup,
            )

        neo4j_deleted = [n.node_id for n in deleted_nodes if n.node_id]
        await self.qdrant.delete_points(
            collection_name=collection_name, point_ids=neo4j_deleted
        )

        logger.info(f"Successfully deleted {len(neo4j_deleted)} nodes.")

        return deleted_nodes

    async def close(self) -> None:
        """
        Closes the connections to underlying components, such as the graph database.
        """
        await self.neo4j.close()
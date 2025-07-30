import asyncio
import copy
import functools
import itertools
import os
import re
from datetime import datetime
from time import time
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Concatenate,
    Coroutine,
    Dict,
    Iterable,
    List,
    Optional,
    ParamSpec,
    Self,
    Set,
    Tuple,
    TypeVar,
    cast,
)

import httpx
import tiktoken
from cachetools import TTLCache

from ragchat.definitions import (
    Flow,
    Id,
    Message,
    Node,
    Point,
    UrlKey,
    UrlKeyModel,
)
from ragchat.log import get_logger

logger = get_logger(__name__)
URL_MODELS_CACHE: TTLCache[str, Any] = TTLCache(maxsize=128, ttl=900)


def flatten(items: List[Any]) -> List[Any]:
    """Flattens a list that may contain nested lists into a single flat list."""
    if not items:
        return items
    return list(
        itertools.chain.from_iterable(
            [item] if not isinstance(item, list) else item for item in items
        )
    )


T = TypeVar("T")


def get_unique(items: List[T | List[T]]) -> List[T]:
    """Flattens a list and returns unique items while preserving their original order."""
    if not items:
        return []

    flat_items = flatten(items)

    unique_items = []
    for x in flat_items:
        if x not in unique_items:
            unique_items.append(x)

    return unique_items


S = TypeVar("S")  # Represents the 'self' instance type
P = ParamSpec("P")  # Represents the remaining parameters of the decorated method
R = TypeVar("R")  # Represents the return type of the decorated method

AsyncMethod = Callable[Concatenate[S, P], Coroutine[Any, Any, R]]


def retry(
    retries: int = 3, msg_arg: Optional[str] = None
) -> Callable[[AsyncMethod[S, P, R]], AsyncMethod[S, P, R]]:
    """
    Retries an async function with exponential backoff.

    Args:
        retries (int): The total number of attempts (initial + retries). Must be positive.
        msg_arg (str, optional): Keyword argument name to inject the previous error string.

    Returns:
        Callable: The decorator function.
    """
    if not isinstance(retries, int) or retries <= 0:
        logger.warning(f"Invalid retries value provided: {retries}. Using default 3.")
        retries = 3

    def decorator(func: AsyncMethod[S, P, R]) -> AsyncMethod[S, P, R]:
        @functools.wraps(func)
        async def wrapper(self: S, *args: P.args, **kwargs: P.kwargs) -> R:
            attempt_num = 1
            last_error = None

            while attempt_num <= retries:
                try:
                    call_kwargs = kwargs

                    if last_error and msg_arg is not None:
                        call_kwargs = copy.copy(kwargs)
                        call_kwargs[msg_arg] = f"\n\n{str(last_error)}"

                    return await func(self, *args, **call_kwargs)

                except Exception as e:
                    last_error = e

                    if (
                        hasattr(self, "retry_on")
                        and self.retry_on
                        and not any(
                            isinstance(e, exc_type) for exc_type in self.retry_on
                        )
                    ):
                        raise

                    if attempt_num == retries:
                        raise ValueError(
                            f"Function {func.__name__} failed after {attempt_num} attempts. Last error: {str(e)}"
                        ) from e

                    logger.warning(
                        f"Attempt {attempt_num}/{retries} for {func.__name__}: {str(e)}",
                        stacklevel=2,
                    )

                    if isinstance(e, ValueError):
                        delay = 0.5
                    else:
                        delay = max(0, 2**attempt_num - 2)

                    await asyncio.sleep(delay)
                    attempt_num += 1

            raise RuntimeError(
                "This point should not be reached as all attempts should either succeed or raise an error."
            )

        return cast(AsyncMethod[S, P, R], wrapper)

    return decorator


def timeit(
    log_level: int, laps: int = 1
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:
    """
    Decorator factory that logs the execution time of the decorated async function.
    Runs the function multiple times if `laps > 1` to get a more accurate reading.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        laps: The number of times to run the decorated function. Defaults to 1.
              For `laps > 1`, the average execution time is logged.
    """

    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if laps < 1:
                raise ValueError("laps must be at least 1")

            if logger.isEnabledFor(log_level):
                last_result: R
                start_time = time()

                for _ in range(laps):
                    last_result = await func(*args, **kwargs)

                end_time = time()
                total_execution_time = end_time - start_time
                average_execution_time = total_execution_time / laps

                log_message = f"{func.__name__} took {average_execution_time:.3f} seconds (average over {laps} laps)"
                logger.log(log_level, log_message)

                return last_result
            else:
                return await func(*args, **kwargs)

        return async_wrapper

    return decorator


async def _fetch_available_models(
    apis: Iterable[UrlKey], use_cache: bool = True
) -> Dict[str, List[str]]:
    """
    Fetches available models from a list of APIs.
    Returns a dictionary mapping API URLs to lists of model IDs.
    Uses a TTL cache (15 minutes) if `use_cache` is True.
    """
    if not apis:
        return {}

    if use_cache:
        if all(api.url in URL_MODELS_CACHE for api in apis):
            return {api.url: URL_MODELS_CACHE[api.url] for api in apis}

    async def fetch_one(api: UrlKey) -> Tuple[str, List[str]]:
        headers = {"Authorization": f"Bearer {api.key}"}
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{api.url}/models", headers=headers)
                response.raise_for_status()
                resp_json = response.json()
                return api.url, [m["id"] for m in resp_json.get("data", [])]
        except Exception:
            return api.url, []

    results = await asyncio.gather(
        *(fetch_one(api) for api in apis), return_exceptions=False
    )
    result_dict = {url: models for url, models in results}
    if use_cache:
        URL_MODELS_CACHE.update(result_dict)
    return result_dict


async def select_model(
    models: List[str],
    apis: Iterable[UrlKey],
    use_cache: bool = True,
) -> UrlKeyModel:
    """
    Selects the first model from `models` that is available from any of the `apis`.
    Supports "auto" keyword to select the first available model from the next API.

    Args:
        models: A list of model IDs to check, in order of preference. Includes "auto".
        apis: An iterable of `UrlKey` objects representing APIs to check, in order.
        use_cache: If True, uses a TTL cache for available models.

    Returns:
        A `UrlKeyModel` object containing the URL, key, and selected model ID.

    Raises:
        Exception: If no valid model can be selected from the provided lists.
    """

    apis_list = list(apis)

    available_models_by_url: Dict[str, List[str]] = await _fetch_available_models(
        apis_list, use_cache
    )

    for m in models:
        if m.split("/")[-1].lower() == "auto":
            for api in apis_list:
                available_models = available_models_by_url.get(api.url, [])
                if available_models:
                    auto_selected_model = f"openai/{available_models[0]}"
                    logger.info(
                        f"Selected model '{auto_selected_model}' via 'auto' fallback from API {api.url}"
                    )
                    return UrlKeyModel(api.url, api.key, auto_selected_model)
        else:
            model_id_short = m.split("/")[-1]
            for api in apis_list:
                available_models = available_models_by_url.get(api.url, [])
                if model_id_short in available_models:
                    logger.info(f"Selected specific model '{m}' from API {api.url}")
                    return UrlKeyModel(api.url, api.key, m)

    logger.error(
        f"models={models!r}, apis={[('***' if api.key else None, api.url) for api in apis_list]}, "
        f"no valid model could be selected."
    )
    raise Exception("No valid model could be selected.")


def est_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a string using the GPT-4o tokenizer.
    """
    try:
        encoding = tiktoken.get_encoding("o200k_base")
        num_tokens = len(encoding.encode(text))
        return num_tokens
    except Exception as e:
        print(f"An error occurred: {e}")
        return -1


def remove_keys(
    data: dict[str, Any], ks: set[str], in_place: bool = False
) -> dict[str, Any]:
    """
    Recursively removes specified keys from a dictionary and its nested dictionaries/lists.

    Args:
        data: The dictionary to process.
        ks: A set of keys to remove.
        in_place: If True, modifies the dictionary in place; otherwise, operates on a deep copy.

    Returns:
        The dictionary with specified keys removed.
    """
    if not in_place:
        data = copy.deepcopy(data)

    queue = [data]
    while queue:
        current = queue.pop(0)
        if isinstance(current, dict):
            keys_to_delete = [key for key, _ in current.items() if key in ks]
            for key in keys_to_delete:
                del current[key]
            for value in current.values():
                queue.append(value)
        elif isinstance(current, list):
            queue.extend(current)
    return data


def remove_previous_memories(
    messages: List[Message],
    flow: Optional[Flow] = None,
) -> None:
    """
    Removes previously added memory sections from message content to avoid duplication.
    Adjusts content based on the specified `Flow`.

    Args:
        messages: The list of messages to modify.
        flow: The processing flow (e.g., `Flow.CHAT`, `Flow.FILE`) to determine content format.
    """
    if flow == Flow.CHAT:
        msg = next((msg for msg in messages if msg.role == "system"), None)
        if not msg or not msg.content:
            return
        pattern = r"\[PROMPT\](.*?)\[/PROMPT\]\n\[MEMORIES\].*?\[/MEMORIES\]"
        match = re.search(pattern, msg.content, re.DOTALL)
        if match:
            msg.content = match.group(1).strip()
    elif flow == Flow.FILE:
        msg = next((msg for msg in reversed(messages) if msg.role == "user"), None)
        if not msg or not msg.content:
            return
        pattern = r"\[INPUT\].*?<query>(.*?)</query>.*?\[/INPUT\]"
        match = re.search(pattern, msg.content, re.DOTALL)
        if match:
            msg.content = match.group(1).strip()
    else:
        logger.warning(f"Unsupported flow for remove_previous_memories: {flow}")


def add_new_memories(
    messages: List[Message],
    relevant_memories: List[Node],
    flow: Flow,
) -> None:
    """
    Adds relevant memories (chunks) to the message content, formatting them
    according to the specified `Flow`.

    Args:
        messages: The list of messages to modify.
        relevant_memories: The list of `Node` objects (chunks) to add.
        flow: The processing flow (e.g., `Flow.CHAT`, `Flow.FILE`) for formatting.
    """
    if not relevant_memories:
        return

    if flow == Flow.CHAT:
        msg = next((msg for msg in messages if msg.role == "system"), None)
        if not msg:
            logger.warning("No system message found to add chat memories.")
            return

        memories_text = "\n\n-----\n\n".join(str(chunk) for chunk in relevant_memories)

        if not msg.content or not msg.content.strip().startswith("[PROMPT]"):
            msg.content = f"[PROMPT]\n{msg.content}\n[/PROMPT]"

        msg.content = f"{msg.content}\n[MEMORIES]\n{memories_text}\n[/MEMORIES]"

    elif flow == Flow.FILE:
        msg = next((msg for msg in reversed(messages) if msg.role == "user"), None)
        if not msg:
            logger.warning("No user message found to add file memories.")
            return

        memories_text = "\n\n".join(
            f'<source id="{i + 1}">\n{chunk.content}\n</source>'
            for i, chunk in enumerate(relevant_memories)
        )

        if not msg.content or not msg.content.strip().startswith("<query>"):
            msg.content = f"<query>\n{msg.content}\n</query>"

        msg.content = (
            f"[INPUT]\n\n{msg.content}\n\n{memories_text}\n\n[/INPUT]\n[OUTPUT]"
        )

    else:
        logger.warning(f"Unsupported flow for add_new_memories: {flow}")
        return

    logger.debug(f"message with memories:\n{msg}")


def is_iso_datetime_string(s: str) -> bool:
    """Checks if a string is a valid ISO 8601 datetime string."""
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def find_files(directory: str, extension: Optional[str] = None) -> list[str]:
    """
    Finds files in a given directory and its subdirectories, optionally filtered by extension.
    Returns a sorted list of full file paths.
    """
    found_paths = []
    if not os.path.isdir(directory):
        logger.warning(f"Search directory not found: '{directory}'")
        return []

    try:
        for root, _, files in os.walk(directory):
            for file in files:
                full_path = os.path.join(root, file)
                if extension:
                    if full_path.lower().endswith(f".{extension.lower()}"):
                        found_paths.append(full_path)
                else:
                    found_paths.append(full_path)
    except OSError as e:
        logger.error(f"Error accessing directory '{directory}': {e}")

    if not found_paths and extension:
        logger.warning(f"No .{extension} files found in {directory}")
    elif not found_paths:
        logger.warning(f"No files found in {directory}")

    found_paths.sort()
    return found_paths


def match_file(
    search_term: str, search_directory: str, extension: Optional[str] = None
) -> str | None:
    """
    Matches a single file within a directory based on a substring `search_term` in its full path.

    Args:
        search_term: The substring to find within file paths (e.g., "my_file.json", "my_file").
        search_directory: The directory to search within.
        extension: Optional. If provided, only files with this extension are considered.

    Returns:
        The full path to the matched file if exactly one unique file is found.
        Returns None if no files match or if multiple files match (to avoid ambiguity).
    """
    if not search_term:
        logger.warning("Search term cannot be empty.")
        return None

    all_files_in_dir = find_files(search_directory, extension)
    matched_files = [f for f in all_files_in_dir if search_term in f]

    if not matched_files:
        logger.warning(
            f"No files matching '{search_term}' found in '{search_directory}'"
            f"{f' with extension .{extension}' if extension else ''}."
        )
        return None
    elif len(matched_files) > 1:
        logger.warning(
            f"Multiple files matching '{search_term}' found in '{search_directory}':"
        )
        for f in matched_files:
            logger.warning(f"  - {f}")
        logger.warning(
            "Please provide a more specific search term to ensure a unique match."
        )
        return None
    else:
        file_path = matched_files[0]
        if not os.path.exists(file_path):
            logger.warning(f"Matched file not found or accessible: {file_path}")
            return None
        logger.info(f"Successfully matched file: {file_path}")
        return file_path


def clean_file_name(name: str) -> str:
    """Cleans a string to be safe for filenames, keeping only alphanumerics, dashes, and underscores."""
    return "".join(c for c in name.split("/")[-1] if c.isalnum() or c in ("-", "_"))


async def _custom_as_completed(
    tasks: List[asyncio.Task[Any]],
) -> AsyncGenerator[asyncio.Task[Any], None]:
    """
    A custom implementation of `asyncio.as_completed` using `asyncio.wait`.
    Yields tasks as they complete.
    """
    task_set = set(tasks)
    while task_set:
        done, pending = await asyncio.wait(
            task_set, return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            yield task
        task_set = pending


class NoContext:
    """
    A no-operation asynchronous context manager.
    Useful when an async context manager (e.g., a semaphore) is optional.
    """

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        pass


def rescale_similarity(
    points: List[Point] | List[Node],
    ids: Optional[Set[Id]] = None,
    max_score: float = 1.0,
) -> None:
    """
    Rescales the similarity scores of `Point` or `Node` objects.
    Scores are rescaled relative to the maximum similarity found among valid points,
    such that the highest score becomes `max_score`.

    Args:
        points: A list of `Point` or `Node` objects, each with a `similarity` attribute.
        ids: An optional set of `node_id`s. If provided, only points with IDs in this set are considered for rescaling.
        max_score: The target maximum similarity score after rescaling. Defaults to 1.0.
    """
    valid_points = [p for p in points if (not ids or p.node_id in ids) and p.similarity]
    max_sim = max(
        (cast(float, p.similarity) for p in valid_points),
        default=0.0,
    )

    factor = max_score / max_sim if max_sim else 0.0

    for p in valid_points:
        assert p.similarity
        p.similarity = p.similarity * factor
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic_settings import BaseSettings, SettingsConfigDict
from rapidfuzz import fuzz, process

from ragchat import prompts
from ragchat.definitions import (
    IndexedMetadata,
    Language,
    Message,
    Node,
    NodeType,
    Relation,
    Translations,
)
from ragchat.log import get_logger
from ragchat.utils import get_unique

logger = get_logger(__name__)


class ParserSettings(BaseSettings):
    score_cutoff: int = 80
    chunk_char_size: int = 2000
    max_chars_fact: int = 256
    max_chars_entity: int = 99

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="PARSER_")


settings = ParserSettings()

node_type_translations: List[Translations] = [
    prompts._entity,
    prompts._entities,
    prompts._fact,
    prompts._facts,
    prompts._chunk,
    prompts._chunks,
]


def split_name_descriptor(s: str) -> Tuple[str, Optional[str]]:
    """Splits a string into a name and an optional descriptor in parentheses."""
    matches = re.match(r"([^(]+)\s*\((.*?)\).*$", s)
    if matches:
        name = matches.group(1).strip()
        descriptor = matches.group(2).strip()

        # Handle edge case where name might be numeric and descriptor might be the actual name
        if descriptor[:1].isdigit() or (
            descriptor.startswith("-") and descriptor[1:2].isdigit()
        ):
            _ = name
            name = descriptor
            descriptor = _

        return name, descriptor

    return s, None


def str_to_node(
    item: str,
    node_type: NodeType,
    metadata: IndexedMetadata,
    language: Language = Language.ENGLISH,
) -> Node:
    """Creates a Node object from a string and metadata."""
    item = item.strip()
    name, descriptor = split_name_descriptor(item)

    reserved_names = [t.get(language) for t in node_type_translations]

    if name.lower() in reserved_names:
        raise ValueError(f"The name cannot be '{name}'. It is a reserved word.")

    content = None
    if node_type == NodeType.ENTITY:
        if descriptor is None:
            raise ValueError(
                f"Invalid entity format: '{item}' "
                "Each entity should be listed separately with a single name and a single type: `name (type)`"
            )
        content = f"{name} ({descriptor})"

    node = Node.from_metadata(
        metadata=metadata, node_type=node_type, content=content or item
    )
    return node


def header_items_to_markdown(
    header: str, items: List[Any], header_level: str = "##", bullet_char: str = "-"
) -> str:
    """Converts a list of items into markdown format with the given header."""
    markdown = f"{header_level} {header}\n"
    markdown += "\n".join([f"{bullet_char} {item}" for item in items])
    return markdown


def markdown_to_heading_items(
    markdown: str,
    match_headings: Optional[List[str]] = None,
    headings_pool: Optional[List[str]] = None,
    match_items: Optional[List[str]] = None,
    items_pool: Optional[List[str]] = None,
    mutually_exclusive: bool = False,
    exclude_nones: bool = True,
    score_cutoff: int = settings.score_cutoff,
) -> Dict[str, List[str]]:
    """
    Parses markdown text to extract list items organized by headings,
    with optional fuzzy validation against pools or exact (fuzzy) matching sets.
    """
    lines = markdown.split("\n")
    list_item_pattern = re.compile(r"^\s*[-*+]\s+(.*?)$")
    heading_pattern = re.compile(r"^(#{1,6})\s+(.*?)$")

    result: Dict[str, List[str]] = {}
    current_heading: Optional[str] = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped.strip().strip("'\"").lower() == "none":
            continue

        heading_match = heading_pattern.match(line)
        if heading_match:
            current_heading = " ".join(
                heading_match.group(2).strip().strip("'\"").split()
            )
            if current_heading not in result:
                result[current_heading] = []
            continue

        if current_heading:
            match = list_item_pattern.match(line)
            if match:
                item = " ".join(match.group(1).strip().split())
                result[current_heading].append(item)

    parsed_headings: List[str] = list(result.keys())
    parsed_items: List[str] = get_unique(list(result.values()))

    def check_pool(items_to_check: List[str], pool: List[str], item_type: str) -> None:
        if not pool:
            if items_to_check:
                raise ValueError(
                    f"Found {item_type}s {items_to_check} but {item_type} pool is empty."
                )
            return

        invalid_items: Set[str] = set()
        for item in items_to_check:
            match = process.extractOne(
                item, pool, scorer=fuzz.ratio, score_cutoff=score_cutoff
            )
            if match is None:
                invalid_items.add(item)
        if invalid_items:
            logger.debug(
                f"Found {item_type}s not in the allowed pool: "
                f"{list(invalid_items)}. Pool: {pool}"
            )
            raise ValueError(f"Select only from the allowed {item_type}s: {pool}.")

    def check_match(parsed: List[str], expected: List[str], item_type: str) -> None:
        unmatched_parsed = []
        if expected:
            for item in parsed:
                match = process.extractOne(
                    item, expected, scorer=fuzz.ratio, score_cutoff=score_cutoff
                )
                if match is None:
                    unmatched_parsed.append(item)
        elif parsed:
            unmatched_parsed = parsed

        if unmatched_parsed:
            logger.debug(
                f"Found unexpected {item_type}s: "
                f"Found {unmatched_parsed}. Expected: {expected}"
            )
            raise ValueError(f"Adhere strictly to {item_type}s: {expected}")

        unmatched_expected = []
        if parsed:
            for item in expected:
                match = process.extractOne(
                    item, parsed, scorer=fuzz.ratio, score_cutoff=score_cutoff
                )
                if match is None:
                    unmatched_expected.append(item)
        elif expected:
            unmatched_expected = expected

        if unmatched_expected:
            logger.debug(
                f"Missing {item_type}s: Found: {parsed}. Missing {unmatched_expected}"
            )
            raise ValueError(f"Adhere strictly to {item_type}s: {expected}")

    if headings_pool is not None:
        check_pool(parsed_headings, headings_pool, "heading")

    if items_pool is not None:
        check_pool(parsed_items, items_pool, "item")

    if match_headings is not None:
        check_match(parsed_headings, match_headings, "heading")

    if match_items is not None:
        check_match(parsed_items, match_items, "item")

    if mutually_exclusive:
        all_items = [item for items in result.values() for item in items]
        if len(set(all_items)) != len(all_items):
            counts: dict[str, int] = {}
            duplicates = set()
            for item in all_items:
                counts[item] = counts.get(item, 0) + 1
                if counts[item] > 1:
                    duplicates.add(item)
            logger.debug(
                f"Items are not mutually exclusive across headings. Duplicates found: {list(duplicates)}"
            )
            raise ValueError("Items cannot repeat across headings.")

    if exclude_nones:
        cleaned_result = {}
        for k, v in result.items():
            filtered_items = [item for item in v if item and item.lower() != "none"]
            if filtered_items:
                cleaned_result[k] = filtered_items
        result = cleaned_result

    return result


def markdown_to_nodes(
    markdown: str,
    indexed_metadata: IndexedMetadata,
    node_type: Optional[NodeType] = None,
    match_items: Optional[List[str]] = None,
    items_pool: Optional[List[str]] = None,
    mutually_exclusive: bool = False,
    exclude_nones: bool = True,
    score_cutoff: int = settings.score_cutoff,
    language: Language = Language.ENGLISH,
) -> Dict[NodeType, List[Node]]:
    """
    Parses markdown text into a dictionary mapping NodeTypes to lists of Node objects,
    using `indexed_metadata` for Node creation.
    """
    heading_items = markdown_to_heading_items(
        markdown=markdown,
        headings_pool=[t.get(language) for t in node_type_translations],
        match_items=match_items,
        items_pool=items_pool,
        mutually_exclusive=mutually_exclusive,
        exclude_nones=exclude_nones,
        score_cutoff=score_cutoff,
    )

    max_chars = {
        NodeType.FACT: settings.max_chars_fact,
        NodeType.ENTITY: settings.max_chars_entity,
    }

    nodes_dict: Dict[NodeType, List[Node]] = {}
    for heading, items_list in heading_items.items():
        if not items_list and exclude_nones:
            continue

        current_node_type = node_type
        if not current_node_type:
            if Translations.is_any(heading, [prompts._chunk, prompts._chunks]):
                current_node_type = NodeType.CHUNK
            elif Translations.is_any(heading, [prompts._fact, prompts._facts]):
                current_node_type = NodeType.FACT
            elif Translations.is_any(heading, [prompts._entity, prompts._entities]):
                current_node_type = NodeType.ENTITY

        if not current_node_type:
            logger.warning(f"Missing NodeType and cannot be inferred from: {heading}")
            raise ValueError("Pay attention to the instructions.")

        if not nodes_dict.get(current_node_type):
            nodes_dict[current_node_type] = []

        for item_str in items_list:
            if max_chars.get(current_node_type) and max_chars[current_node_type] < len(
                item_str
            ):
                logger.warning(
                    f"Item exceeding {max_chars[current_node_type]} characters: {item_str[: max_chars[current_node_type]]}..."
                )
                raise ValueError("Be concise!")
            nodes_dict[current_node_type].append(
                str_to_node(item_str, current_node_type, indexed_metadata)
            )

    return nodes_dict


def markdown_to_relation(
    markdown: str,
    summary: str,
    indexed_metadata: IndexedMetadata,
    chunk_content: str,
    min_chars: int = 32,
    score_cutoff: int = settings.score_cutoff,
) -> Optional[Relation]:
    """
    Parses markdown text, summary, chunk content, and `indexed_metadata` into a Relation object.
    """
    m = markdown
    if len(m) < min_chars:
        return None

    nodes_dict = markdown_to_nodes(
        markdown=m,
        indexed_metadata=indexed_metadata,
        exclude_nones=True,
        score_cutoff=score_cutoff,
    )

    if not nodes_dict.get(NodeType.FACT):
        logger.warning(f"No facts found in markdown:\n{markdown}")
        raise ValueError("At least one fact listed under `## Facts`")

    if not nodes_dict.get(NodeType.ENTITY):
        logger.warning(f"No entities found in markdown:\n{markdown}")
        raise ValueError(
            "At least one entity listed under `## Entities`, entities with format `- name (type)`"
        )

    chunk = str_to_node(chunk_content, NodeType.CHUNK, indexed_metadata)
    chunk.summary = summary

    relation = Relation(
        chunk=chunk,
        facts=nodes_dict.get(NodeType.FACT, []),
        entities=nodes_dict.get(NodeType.ENTITY, []),
    )

    return relation


def _find_split(window: str, delimiters: list[str], min_window_size: int) -> int:
    """Finds an appropriate split point in a text window based on delimiters."""
    window_size = len(window)
    for delimiter in delimiters:
        idx = window.rfind(delimiter)
        if min_window_size < idx:
            window_size = idx
            break
    return window_size


def chunk_text(text: str, chunk_char_size: Optional[int] = None) -> List[str]:
    """Splits text into chunks, respecting markdown headings and paragraphs."""
    chunks = []
    start = 0
    text_length = len(text)
    chunk_char_size = chunk_char_size or settings.chunk_char_size
    while start < text_length:
        end = start + chunk_char_size
        if text_length < end:
            chunks.append(text[start:])
            break

        current_window = text[start:end]
        delimiters = [
            "\n# ",
            "\n## ",
            "\n### ",
            "\n\n\n\n",
            "\n\n\n",
            "\n\n",
            "\n",
            ". ",
            " ",
        ]
        end = start + _find_split(current_window, delimiters, chunk_char_size // 2)

        chunk = text[start:end]
        if chunk:
            if 0 < len(chunks) and (len(chunks[-1]) + len(chunk)) < chunk_char_size:
                chunks[-1] += chunk
            else:
                chunks.append(chunk)
        start = end

    return chunks


def dicts_to_messages(messages: List[Dict[str, Any] | Message]) -> List[Message]:
    """Converts a list of dictionaries and/or Message objects into a list of Message objects."""
    if not messages:
        return []

    new_messages = []
    for msg in messages:
        if isinstance(msg, Message):
            new_messages.append(msg)
        elif isinstance(msg, dict):
            new_messages.append(Message(**msg))
        else:
            raise ValueError(f"Cannot convert message of type {type(msg)} to Message")
    return new_messages


def messages_to_dicts(messages: List[Message | Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts a list of Message objects and/or dictionaries into a list of dictionaries."""
    if not messages:
        return []

    new_dicts = []
    for msg in messages:
        if isinstance(msg, dict):
            new_dicts.append(msg)
        elif isinstance(msg, Message):
            new_dicts.append(msg.model_dump(mode="json", exclude_none=True))
        else:
            raise ValueError(f"Cannot convert message of type {type(msg)} to dict")
    return new_dicts


def messages_to_user_text(
    messages: List[Message],
    limit: int = 3,
) -> str:
    """Creates a string from the last N user messages."""
    s = "\n\n".join(
        [f"{m.role}: {m.content}" for m in messages if m.role == "user"][-limit:]
    )

    return s
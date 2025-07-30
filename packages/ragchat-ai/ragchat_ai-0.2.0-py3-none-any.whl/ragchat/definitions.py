import re
import uuid
from enum import Enum
from logging import getLogger
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Literal,
    NamedTuple,
    Optional,
    Self,
    Set,
    Tuple,
    TypeVar,
    cast,
)
from uuid import UUID

import base58
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticUndefined

logger = getLogger(__name__)

__all__ = ["Message"]

####################################
# --- Flows & General ---
####################################

Id = str | int

PRIMITIVE_TYPES: Tuple[type, ...] = (str, int, float, bool)

Primitive = str | int | float | bool


class classproperty:
    """A decorator that allows a method to be accessed as a property of the class."""

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func

    def __get__(self, instance: Any, cls: Any = None) -> Any:
        if cls is None:
            cls = type(instance)
        return self.func(cls)


class Flow(Enum):
    """Enum representing different operational flows."""

    FILE = "file"
    CHAT = "chat"

    def __str__(self) -> str:
        return self.value


def indexed_keys(flow: Optional[Flow] = None) -> Set[str]:
    """
    Returns a set of keys used for indexing, optionally filtered by flow type.
    """
    common = {"node_id", "search_space"}
    flow_specific_keys_map = {
        Flow.CHAT: {"user_id", "chat_id"},
        Flow.FILE: {"folder_id", "user_id", "file_id"},
    }

    if flow is None:
        return common | set.union(*flow_specific_keys_map.values())
    else:
        match flow:
            case Flow.CHAT:
                return common | flow_specific_keys_map[Flow.CHAT]
            case Flow.FILE:
                return common | flow_specific_keys_map[Flow.FILE]
            case _:
                raise ValueError(f"Unhandled flow type: {flow}")


def search_space_key(flow: Flow) -> str:
    """
    Returns the primary key used to define the search space for a given flow.
    """
    match flow:
        case Flow.CHAT:
            return "user_id"
        case Flow.FILE:
            return "folder_id"
        case _:
            raise NotImplementedError(
                f"search_space_key not implemented for flow: {flow}"
            )


class Message(BaseModel):
    """Represents a message with content and a role."""

    content: str
    role: Literal["assistant", "user", "system", "tool", "function"]


class MessageClassification(Enum):
    """Enum representing the classification of a message."""

    STATEMENT = "statement"
    QUESTION = "question"
    MIXED = "mixed"
    NONE = "none"

    def __str__(self) -> str:
        return self.value


T = TypeVar("T", bound=BaseModel)


class _indexModel(BaseModel):
    """
    Base class for models that map fields and derive a search space.
    """

    flow: Flow = Field(None)  # type: ignore
    search_space: UUID = Field(None)  # type: ignore
    _search_space_dict: Dict[str, str] = PrivateAttr()
    _nested_fields: str = PrivateAttr()

    def model_post_init(self, _: Any) -> None:
        """
        Initializes flow and search_space after model validation.
        """
        nested_fields = getattr(self, self._nested_fields, None)
        self.flow = self.flow or getattr(nested_fields, "_flow", None)

        if self.flow is None:
            raise AssertionError("Flow could not be determined in model_post_init")

        k = search_space_key(self.flow)
        v = getattr(nested_fields, k, None) or getattr(self, k, None)

        if not k or v is None:
            raise ValueError(f"Missing key '{k}' or value is None")

        self._search_space_dict = {k: v}
        self.search_space = uuid.uuid5(uuid.NAMESPACE_DNS, f"{k}:{v}")

    @classmethod
    def required_fields(cls) -> Set[str]:
        """
        Returns a set of field names that are required (no default value or factory).
        """
        return {
            field_name
            for field_name, field_info in cls.model_fields.items()
            if field_info.default is PydanticUndefined
            and field_info.default_factory is None
        }

    def this_indexed_fields(self) -> Dict[str, Any]:
        """
        Returns a dictionary of fields from the model that are designated for indexing.
        """
        indexed_keys_set = set(indexed_keys(self.flow))
        result = {}

        # 1. Check keys from the model's direct attributes (Pydantic fields of 'self')
        for key in self.__class__.model_fields:
            if key in indexed_keys_set and hasattr(self, key):
                result[key] = getattr(self, key)

        # 2. Check keys from self.fields (if it's another Pydantic BaseModel instance)
        fields_obj = getattr(self, self._nested_fields, None)
        if isinstance(fields_obj, BaseModel):
            for key in fields_obj.__class__.model_fields:
                if key in indexed_keys_set and hasattr(fields_obj, key):
                    # This will overwrite if the key was already in result from step 1,
                    # giving precedence to values found within self.fields.
                    result[key] = getattr(fields_obj, key)

        return result


####################################
# --- Metadata and Filters ---
####################################

ALLOWED_KEY_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class _baseMetadata(BaseModel):
    """
    Base class for metadata models, allowing extra fields and validating their format and type.
    """

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_extra_fields(self) -> Self:
        """
        Validates that any extra fields conform to naming conventions and have primitive types.
        """
        if not self.model_extra:
            return self

        allowed_value_types = PRIMITIVE_TYPES

        for key, value in self.model_extra.items():
            if not isinstance(key, str):
                raise ValueError(
                    f"Custom field key must be a string, got {type(key).__name__} for key '{key}'."
                )

            if not ALLOWED_KEY_REGEX.fullmatch(key):
                raise ValueError(
                    f"Custom field key '{key}' contains invalid characters or format. "
                    f"Keys must match regex '{ALLOWED_KEY_REGEX.pattern}'."
                )

            if not isinstance(value, allowed_value_types):
                raise ValueError(
                    f"Custom field '{key}' has an invalid value type. "
                    f"Expected one of {[t.__name__ for t in allowed_value_types]}, but got {type(value).__name__}."
                )

        return self


class ChatMetadata(_baseMetadata):
    """Metadata fields specific to the `chat` flow."""

    _flow: ClassVar[Flow] = Flow.CHAT

    user_id: Id = Field(description="`Indexed` A user ID is an isolated search space.")
    chat_id: Optional[Id] = Field(
        default=None, description="`Indexed` Metadata for filtering."
    )


class FileMetadata(_baseMetadata):
    """Metadata fields specific to the `file` flow."""

    _flow: ClassVar[Flow] = Flow.FILE

    path: str = Field(description="Needed to process the file.")
    folder_id: Id = Field(
        description="`Indexed` A folder ID is an isolated search space."
    )
    user_id: Optional[Id] = Field(
        default=None, description="`Indexed` Metadata for filtering."
    )
    file_id: Optional[Id] = Field(
        default=None, description="`Indexed` Metadata for filtering."
    )
    title: Optional[str] = Field(default=None, description="Metadata for filtering.")


Metadata = ChatMetadata | FileMetadata


class IndexedMetadata(_indexModel):
    """
    Container for flow-specific metadata fields.
    """

    metadata: Metadata
    _nested_fields: str = PrivateAttr("metadata")


class Operator(Enum):
    """Enum representing comparison operators for filtering."""

    EQ = "="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    IN = "in"

    def __str__(self) -> str:
        return self.value


class Condition(BaseModel):
    """Represents an operator-value filter condition."""

    operator: Operator
    value: Primitive | List[Primitive]

    @model_validator(mode="after")
    def validate_operator_value_compatibility(self) -> Self:
        """
        Validates that the operator and value types are compatible.
        """
        if self.operator == Operator.IN:
            if not isinstance(self.value, list):
                raise ValueError(
                    f"Operator '{self.operator.name}' requires a list value, "
                    f"but got {type(self.value).__name__}."
                )
        elif self.operator in (Operator.EQ, Operator.LT, Operator.GT):
            if isinstance(self.value, list):
                raise ValueError(
                    f"Operator '{self.operator.name}' requires a single value, "
                    f"but got a list."
                )
        return self


FilterField = Primitive | List[Primitive] | List[Condition]
_filter_adapter: TypeAdapter[FilterField] = TypeAdapter(FilterField)


class _baseFilters(BaseModel):
    """
    Base class for filter models, allowing extra fields and validating their format and Filter type.
    """

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_extra_fields(self) -> Self:
        """
        Validates that any extra fields conform to naming conventions and are valid Filter types.
        """
        if not self.model_extra:
            return self

        for key, value in self.model_extra.items():
            if not isinstance(key, str):
                raise ValueError(
                    f"Filter key must be a string, got {type(key).__name__} for key '{key}'."
                )

            if not ALLOWED_KEY_REGEX.fullmatch(key):
                raise ValueError(
                    f"Filter key '{key}' contains invalid characters or format. "
                    f"Keys must match regex '{ALLOWED_KEY_REGEX.pattern}'."
                )

            try:
                _filter_adapter.validate_python(value)
            except (ValidationError, ValueError) as e:
                raise ValueError(
                    f"Filter key '{key}' has an invalid value. "
                    f"Expected a valid Filter type, but got {value}. "
                    f"Validation error: {e}"
                ) from e

        return self


class ChatFilters(_baseFilters):
    """Filter fields specific to the `chat` flow."""

    _flow: Flow = PrivateAttr(Flow.CHAT)

    user_id: Optional[FilterField] = Field(
        None, description="`Indexed` A user ID is an isolated search space."
    )
    chat_id: Optional[FilterField] = Field(
        None, description="`Indexed` Metadata for filtering."
    )


class FileFilters(_baseFilters):
    """Filter fields specific to the `file` flow."""

    _flow: Flow = PrivateAttr(Flow.FILE)

    folder_id: Optional[FilterField] = Field(
        None,
        description="`Indexed` A folder is an isolated search space. Not required only for read operations.",
    )
    user_id: Optional[FilterField] = Field(
        default=None, description="`Indexed` Metadata filter."
    )
    file_id: Optional[FilterField] = Field(
        default=None, description="`Indexed` Metadata filter."
    )
    title: Optional[FilterField] = Field(default=None, description="Metadata filter.")
    path: Optional[FilterField] = Field(default=None, description="Metadata filter.")


Filters = ChatFilters | FileFilters


class IndexedFilters(_indexModel):
    """
    Container for flow-specific filter fields, supporting conversion to standardized formats.
    """

    filters: Filters
    _nested_fields: str = PrivateAttr("filters")

    def std_conditions(self) -> Dict[str, List[Condition]]:
        """
        Converts filters into a dictionary where keys map to a list of Condition objects.
        Handles both direct conditions and primitive/list values by converting them to Conditions.
        """

        def _normalize_primitive(value: Any) -> Primitive:
            if isinstance(value, uuid.UUID):
                return str(value)
            if isinstance(value, (str, int, float, bool)):
                return value
            raise TypeError(
                f"Unsupported type for primitive normalization: {type(value)}"
            )

        def _normalize_list_of_primitives(values: List[Any]) -> List[Primitive]:
            return [_normalize_primitive(v) for v in values]

        def _to_list_of_conditions(value: FilterField) -> List[Condition]:
            if isinstance(value, list):
                if value and isinstance(value[0], Condition):
                    return cast(List[Condition], value)
                else:
                    value_as_primitive_list = _normalize_list_of_primitives(value)
                    return [
                        Condition(operator=Operator.IN, value=value_as_primitive_list)
                    ]
            else:
                return [
                    Condition(operator=Operator.EQ, value=_normalize_primitive(value))
                ]

        standardized_filters: Dict[str, List[Condition]] = {}

        # Process extra fields
        if self.model_extra:
            extra_filters = {
                k: _to_list_of_conditions(v)
                for k, v in self.model_extra.items()
                if v is not None
            }
            standardized_filters.update(extra_filters)

        # Process defined fields that were set and are in the indexed keys
        defined_filters = {
            k: _to_list_of_conditions(v)
            for k, v in self.this_indexed_fields().items()
            if v is not None
        }
        standardized_filters.update(defined_filters)

        return standardized_filters

    def std_dict(self) -> Dict[str, Any]:
        """
        Converts filters into a flattened dictionary where keys map to primitive values or lists of primitives.
        Operators are discarded, and multiple conditions for a key are combined into a list.
        """
        conditions = self.std_conditions()
        standardized_dict: Dict[str, Any] = {}

        for key, cond_list in conditions.items():
            flattened_values: List[Primitive] = []
            for cond in cond_list:
                if isinstance(cond.value, list):
                    flattened_values.extend(cond.value)
                else:
                    flattened_values.append(cond.value)

            if len(flattened_values) == 1:
                standardized_dict[key] = flattened_values[0]
            elif len(flattened_values) > 1:
                standardized_dict[key] = flattened_values

        return standardized_dict


####################################
# --- Nodes and Relations ---
####################################


class NodeType(Enum):
    """Enum representing the possible types of nodes."""

    FACT = "fact"
    CHUNK = "chunk"
    ENTITY = "entity"

    def __str__(self) -> str:
        return self.value


class EmbeddingType(Enum):
    """Enum representing different types of embeddings."""

    DENSE = "dense"
    SPARSE = "sparse"

    def __str__(self) -> str:
        return self.value


class Embedding(BaseModel):
    """Represents a vector embedding with its type and optional name."""

    type: EmbeddingType
    vec: Any
    name: Optional[str] = None

    @staticmethod
    def get(
        embs: Optional[List["Embedding"]],
        type: Optional[EmbeddingType] = None,
        name: Optional[str] = None,
    ) -> List[Any]:
        """
        Retrieves a list containing the vector of an embedding matching the specified type and/or name.
        Raises ValueError if no matching embedding is found or if criteria are missing.
        """
        if not embs:
            raise ValueError("Missing embeddings.")

        if type is None and name is None:
            raise ValueError("At least one of 'type' or 'name' must be provided.")

        found_embedding = next(
            (
                emb
                for emb in embs
                if ((type is None) or (emb.type == type))
                and ((name is None) or (emb.name == name))
            ),
            None,
        )

        if found_embedding:
            return [found_embedding.vec]

        criteria_str = []
        if type:
            criteria_str.append(f"type='{type.value}'")
        if name:
            criteria_str.append(f"name='{name}'")

        raise ValueError(
            f"No embedding found matching criteria: {', '.join(criteria_str)}"
        )


class Node(_indexModel):
    """
    Internal structure representing a node with its properties, including content, type, and associated metadata.
    """

    node_type: NodeType
    flow: Flow
    content: str
    summary: Optional[str] = None
    embeddings: Optional[List[Embedding]] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    similarity: Optional[float] = None
    # indexed fields
    node_id: Optional[UUID] = None
    user_id: Optional[Id] = None
    chat_id: Optional[Id] = None
    folder_id: Optional[Id] = None
    file_id: Optional[Id] = None
    # extra
    custom: Optional[Dict[str, Primitive]] = None

    _descriptor: Optional[str] = PrivateAttr(None)
    _hash: UUID = PrivateAttr()
    _nested_fields: str = PrivateAttr("custom")

    @classmethod
    def node_keys(cls, node_type: NodeType, flow: Flow) -> Set[str]:
        """
        Returns a set of keys representing the data fields of the node, excluding private/class variables.
        Adjusts keys based on node type and flow.
        """
        if not node_type:
            raise ValueError("Missing `node_type`.")
        if not flow:
            raise ValueError("Missing `flow`.")

        keys = set(cls.model_fields.keys())
        if node_type != NodeType.CHUNK:
            keys -= {"custom"}
            keys -= indexed_keys(flow)
            keys |= {search_space_key(flow)}
            keys |= {"node_id", "search_space"}

        return keys

    def this_node_keys(self) -> Set[str]:
        """
        Returns the set of data keys relevant to this specific node instance.
        """
        return self.node_keys(self.node_type, self.flow)

    def model_post_init(self, context: Any) -> None:
        """
        Performs post-initialization, including setting the search space and calculating the node hash.
        For CHUNK nodes, the node_id is set to this hash.
        """
        super().model_post_init(context)

        assert self.search_space
        name_string = f"{self.search_space}:{self.node_type.value}:{self.flow.value}:{self.content}"
        self._hash = uuid.uuid5(uuid.NAMESPACE_DNS, name_string)
        if self.node_type == NodeType.CHUNK:
            self.node_id = self._hash

    @classmethod
    def from_metadata(
        cls, metadata: IndexedMetadata, node_type: NodeType, content: str
    ) -> Self:
        """
        Creates a Node instance from provided metadata, node type, and content.
        Populates node fields based on the metadata and node type.
        """
        node_keys = cls.node_keys(node_type, metadata.flow)
        init_args: Dict[str, Any] = (
            {
                "node_type": node_type,
                "flow": metadata.flow,
                "content": content,
            }
            | metadata._search_space_dict
            | metadata.metadata.model_dump(exclude_none=True, include=node_keys)
        )
        if node_type == NodeType.CHUNK:
            init_args.update({
                "custom": metadata.metadata.model_dump(
                    exclude_none=True, exclude=node_keys
                )
            })

        return cls(**init_args)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Node):
            return False
        return self._hash == other._hash

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self._hash < other._hash

    def __hash__(self) -> int:
        return hash(self._hash)

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        """Strips leading/trailing whitespace from the content string."""
        if v is None:
            return None
        return v.strip()

    @field_validator("created_at", "updated_at")
    @classmethod
    def to_millis(cls, value: Optional[int]) -> Optional[int]:
        """
        Validates and converts a timestamp to milliseconds if it appears to be in seconds.
        Raises ValueError for invalid timestamp values.
        """
        if value is None:
            return None

        if not isinstance(value, (int, float)):
            raise ValueError("Timestamp must be an integer or float")

        value = int(value)

        if value <= 1e8 or 1e16 <= value:
            raise ValueError("Invalid timestamp value")

        if 1e14 < value:
            return int(value / 1000)
        elif 1e11 < value:
            return value
        elif 1e8 < value:
            return value * 1000
        raise ValueError("Invalid timestamp value")

    def __str__(self) -> str:
        return self.content or ""


class Point(BaseModel):
    """Represents a graph entry point, typically a node, with an optional similarity score."""

    node_id: UUID
    similarity: Optional[float] = None
    content: Optional[str] = None
    query_content: Optional[str] = None
    group_id: Optional[int] = None


class QueryPoint(BaseModel):
    """Represents a query entry point for searching nodes, including content and embeddings."""

    content: str
    embeddings: List[Embedding]
    node_type: NodeType
    node_id: Optional[List[UUID]] = None
    text_weight: Optional[float] = None
    results: Optional[List[Point]] = None


class Relation(BaseModel):
    """
    Represents a memory unit linking a chunk with associated facts and entities.
    """

    chunk: Node = Field(description="The chunk of the relation")
    facts: List[Node] = Field(description="The facts associated with the chunk")
    entities: List[Node] = Field(description="The entities involved in the relation")
    points: Optional[List[Point]] = None

    def to_list(self, include: Optional[List[NodeType]] = None) -> List[Node]:
        """
        Converts the relation into a list of nodes.
        If 'include' is specified, returns nodes of the specified types in order.
        Otherwise, returns [chunk, facts..., entities...].
        """
        if include is None:
            return [self.chunk] + self.facts + self.entities

        nodes = []
        for node_type in include:
            if node_type == NodeType.CHUNK:
                nodes.append(self.chunk)
            elif node_type == NodeType.FACT:
                nodes.extend(self.facts)
            elif node_type == NodeType.ENTITY:
                nodes.extend(self.entities)
        return nodes


####################################
# --- File operations ---
####################################


class FileStatus(Enum):
    """Enum for possible file processing states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value


class ChunkResult(BaseModel):
    """Represents the result of processing a single chunk within a file."""

    chunk_index: int = Field(..., description="Index of the chunk within the file.")
    id: Optional[UUID] = Field(
        default=None,
        description="ID generated for the upserted chunk.",
    )
    error: Optional[str] = Field(
        default=None, description="Error message if processing this chunk failed."
    )


class FileState(BaseModel):
    """
    Represents the processing state and cumulative results for a single file.
    """

    file_path: str = Field(..., description="Path to the file being processed.")
    task_id: Optional[str] = Field(
        default=None, description="ID of the task processing this file."
    )
    total_chunks: Optional[int] = Field(
        default=None, description="Total number of chunks expected for this file."
    )
    total_bytes: Optional[float] = Field(
        default=None, description="Total bytes in this file."
    )
    processed_bytes: Optional[float] = Field(
        default=None, description="Total bytes processed from this file."
    )
    chunk_results: List[ChunkResult] = Field(
        default_factory=list, description="List of results for each processed chunk."
    )
    status: FileStatus = Field(
        default=FileStatus.PENDING, description="Current status of the file processing."
    )
    error: Optional[str] = Field(
        default=None, description="Error message if status is ERROR or CANCELLED."
    )

    @property
    def is_terminal(self) -> bool:
        """
        Returns True if the file processing is in a final state (completed, error, cancelled).
        """
        return self.status in {
            FileStatus.COMPLETED,
            FileStatus.ERROR,
            FileStatus.CANCELLED,
        }

    @classmethod
    def create_error_state(
        cls, file_path: str, error_msg: str, task_id: Optional[str] = None
    ) -> "FileState":
        """
        Creates a FileState instance representing an error state for a file.
        """
        return cls(
            file_path=file_path,
            task_id=task_id,
            status=FileStatus.ERROR,
            error=error_msg,
            total_chunks=None,
            total_bytes=None,
            processed_bytes=None,
            chunk_results=[],
        )

    @classmethod
    def create_cancelled_state(
        cls,
        file_path: str,
        task_id: Optional[str] = None,
        error_msg: str = "Processing cancelled.",
    ) -> "FileState":
        """
        Creates a FileState instance representing a cancelled state for a file.
        """
        return cls(
            file_path=file_path,
            task_id=task_id,
            status=FileStatus.CANCELLED,
            error=error_msg,
            total_chunks=None,
            total_bytes=None,
            processed_bytes=None,
            chunk_results=[],
        )

    def update_with_chunk_result(self, chunk_result: ChunkResult) -> None:
        """
        Updates the file state by adding a new chunk result and potentially transitioning the status.
        """
        self.chunk_results.append(chunk_result)
        if self.status == FileStatus.PENDING:
            self.status = FileStatus.PROCESSING
        if (
            self.total_chunks is not None
            and len(self.chunk_results) == self.total_chunks
        ):
            self.status = FileStatus.COMPLETED


class SentinelFileState(FileState):
    """A special FileState instance used as a sentinel value for queue termination."""

    def __init__(self) -> None:
        super().__init__(file_path="<sentinel>", status=FileStatus.COMPLETED)


class BatchStatusSummary(BaseModel):
    """
    Provides a summary of the current batch processing status, including file counts, progress, and times.
    """

    total_files: int
    files_done: int
    processing_files: int
    percentage: float
    elapsed_time: float
    remaining_time: Optional[float] = None
    file_states: Dict[str, FileState] = {}
    total_batch_bytes: Optional[float] = Field(
        None, description="The pre-calculated total size of all files in the batch."
    )
    processed_batch_bytes: float = Field(
        0.0, description="Sum of processed_bytes from all FileStates in the batch."
    )


####################################
# --- APIs and models ---
####################################


class UrlKeyModel(NamedTuple):
    """A named tuple for API configuration including URL, API key, and model name."""

    url: str
    key: str
    model: str


class UrlKey(NamedTuple):
    """A named tuple for API configuration including URL and API key."""

    url: str
    key: str


####################################
# --- Prompts ---
####################################


class Language(Enum):
    """Enum representing supported languages."""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def _missing_(cls, value: object) -> "Language":
        """
        Handles variations of language codes (e.g., 'en-US' maps to 'en').
        """
        if isinstance(value, str):
            base_lang = value.split("-")[0].lower()
            for member in cls:
                if member.value == base_lang:
                    return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class Translations(BaseModel):
    """
    A model holding translations for a piece of text across multiple languages.
    """

    en: str
    es: str
    fr: str
    de: str

    def get(self, language: Language) -> str:
        """
        Retrieves the translation for the specified language.
        """
        return str(getattr(self, language.value))

    def is_me(self, text: str) -> bool:
        """
        Checks if the given text matches any of the stored translations (case-insensitive).
        """
        for lang in Language:
            if getattr(self, lang.value.lower()) == text.lower():
                return True
        return False

    @classmethod
    def is_any(cls, text: str, vocab: list["Translations"]) -> bool:
        """
        Checks if the given text matches any translation within a list of Translations objects.
        """
        for v in vocab:
            if v.is_me(text):
                return True
        return False


class Example(BaseModel):
    """Represents an example with input and output translations for a specific flow."""

    flow: Flow = Field(..., description="Type of example")
    example_input: Translations = Field(..., description="Example input translations")
    example_output: Translations = Field(..., description="Example output translations")


class Prompt(BaseModel):
    """
    Represents a prompt with its type, translations, and associated examples.
    """

    prompt_type: Literal["system", "user"] = Field(..., description="Type of prompt")
    prompt: Translations = Field(..., description="Prompt translations")
    examples: List[Example] = Field(..., description="Examples of inputs and outputs")

    def to_str(
        self, flow: Optional[Flow] = None, language: Language = Language.ENGLISH
    ) -> str:
        """
        Generates the full prompt string, including examples filtered by flow and translated to the specified language.
        """
        r = self.prompt.get(language)
        examples = [
            f"[EXAMPLE]\n{e.example_input.get(language)}\n[/EXAMPLE]\n[OUTPUT]\n{e.example_output.get(language)}"
            for e in self.examples
            if not flow or e.flow == flow
        ]
        if not examples:
            return r

        r += "\n\n --- This is an example --- \n\n"
        r += "\n\n --- This is another example --- \n\n".join(examples)
        r += "\n\n --- This was an example --- \n\n"
        return r


####################################
# --- Helper functions ---
####################################


def encode_kv(k: str, v: str) -> str:
    """
    Encodes a key-value pair into a Base58-encoded string prefixed with 'KV' for safe storage.
    The internal format is '{len(k)}:{k}{v}'.
    """
    combined_str = f"{len(k)}:{k}{v}"
    encoded = base58.b58encode(combined_str.encode("utf-8")).decode("utf-8")
    return f"KV{encoded}"


def decode_kv(s: str) -> tuple[str, str]:
    """
    Decodes a 'KV'-prefixed, Base58-encoded string back into the original (key, value) tuple.
    Raises ValueError for invalid formats.
    """
    if not s.startswith("KV"):
        raise ValueError("Encoded string must start with 'KV'")

    encoded_payload = s[2:]

    try:
        decoded_combined_str = base58.b58decode(encoded_payload).decode("utf-8")
    except ValueError as e:
        raise ValueError(f"Invalid encoded KV format: {e}")
    except Exception as e:
        raise ValueError(f"Error decoding KV string: {e}")

    parts = decoded_combined_str.split(":", 1)
    if len(parts) != 2:
        raise ValueError("Invalid decoded KV format: missing key length separator")

    try:
        k_len = int(parts[0])
    except ValueError:
        raise ValueError("Invalid decoded KV format: key length is not an integer")

    full_payload = parts[1]
    if len(full_payload) < k_len:
        raise ValueError(
            "Invalid decoded KV format: payload shorter than declared key length"
        )

    key = full_payload[:k_len]
    value = full_payload[k_len:]

    return key, value
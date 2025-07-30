import asyncio
import copy
import json
from functools import partial
from typing import Any, Callable, List, Optional, cast

from litellm import acompletion
from litellm.types.utils import ChatCompletionMessageToolCall
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ragchat.definitions import (
    Flow,
    IndexedMetadata,
    Language,
    Message,
    MessageClassification,
    Relation,
    UrlKey,
)
from ragchat.log import DEBUG, get_logger
from ragchat.parser import (
    markdown_to_relation,
)
from ragchat.prompts import (
    FACT_ENTITY,
    MSG_CLASSIFICATION,
    SUMMARY,
)
from ragchat.utils import retry, select_model, timeit

logger = get_logger(__name__)


class LlmSettings(BaseSettings):
    base_url: Optional[str] = None
    local_hosts: Optional[List[str]] = ["localhost", "host.docker.internal"]
    port: Optional[int] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    models: Optional[List[str]] = None
    batch_size: int = 16
    temperature: float = 0.0
    custom_msg_classification_prompt: Optional[str] = Field(
        None, description="Replaces MESSAGE_CLASSIFICATION prompt"
    )
    custom_fact_entity_prompt: Optional[str] = Field(
        None, description="Replaces FACT_ENTITY"
    )
    custom_summary_prompt: Optional[str] = Field(None, description="Replaces SUMMARY")
    custom_query_nodes_prompt: Optional[str] = Field(
        None, description="Replaces QUERY_NODES_PROMPT"
    )

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="LLM_")

    @field_validator("models", mode="before")
    @classmethod
    def validate_models(cls, v: str | List[str]) -> List[str]:
        """Validates and converts model input to a list of strings."""
        if isinstance(v, str):
            return [m.strip() for m in v.split(",")]
        return v

    def request_dict(self) -> dict[str, Any]:
        """Returns a dictionary of LLM request parameters."""
        return self.model_dump(
            mode="json",
            include={"base_url", "api_key", "model", "temperature"},
            exclude_none=True,
        )

    async def initialize(self) -> None:
        """Initializes LLM settings by selecting an available model."""
        apis = set()
        if self.base_url and self.api_key:
            apis.add(UrlKey(url=self.base_url, key=self.api_key))
        port = f":{self.port}" if self.port else ""
        for host in self.local_hosts or []:
            apis.add(UrlKey(url=f"http://{host}{port}/v1", key="NA"))

        selected_model = await select_model(
            [self.model] if self.model else (self.models or []), apis
        )
        self.base_url = selected_model.url
        self.api_key = selected_model.key
        self.model = selected_model.model
        logger.info(f"Using model {selected_model.model} from URL {selected_model.url}")


class LLM:
    def __init__(self, settings: Optional[LlmSettings] = None):
        self.settings = settings or LlmSettings()
        self.semaphore: asyncio.Semaphore

    async def initialize(self) -> None:
        """Initializes the LLM client and sets up the concurrency semaphore."""
        await self.settings.initialize()
        self.semaphore = asyncio.Semaphore(self.settings.batch_size)

    @retry(msg_arg="retry_message")
    @timeit(log_level=DEBUG)
    async def generate_response(
        self,
        /,  # mark 'self' as positional-only
        messages: List[Message],
        retry_message: Optional[str] = None,
        parser: Optional[Callable[[str], Any]] = None,
        **kwargs: Any,
    ) -> str | List[ChatCompletionMessageToolCall] | Any:
        """
        Generates a response from the LLM based on provided messages.

        Args:
            messages (List[Message]): Conversation history.
            retry_message (Optional[str]): Additional system prompt for retries.
            parser (Optional[Callable[[str], Any]]): Function to parse the LLM's content response.

        Kwargs:
            model (str): Model to use.
            base_url (str): Base URL for the API.
            api_key (str): API key.
            temperature (float): Sampling temperature.
            max_tokens (int): Maximum tokens to generate.
            tools (List[Dict]): Tools the model can call.
            tool_choice (str | Dict): Controls tool calling.
            strict (bool): Enforce strict validation for tool arguments.

        Returns:
            str | List[ChatCompletionMessageToolCall] | Any: LLM response content, parsed content, or tool calls.
        """

        if retry_message and messages:
            messages = copy.deepcopy(messages)
            has_system_message = False
            for msg in messages:
                if msg.role == "system":
                    msg.content += f"\n\n{retry_message}"
                    has_system_message = True
                    break
            if not has_system_message:
                messages.insert(0, Message(role="system", content=retry_message))

        params = {**self.settings.request_dict(), **kwargs, "stream": False}
        strict = params.pop("strict", True)

        remove = {"flow", "language"}
        params = {k: v for k, v in params.items() if k not in remove}

        response = await acompletion(
            messages=[m.model_dump() for m in messages], **params
        )
        message = response.choices[0].message

        system_msgs = [m for m in messages if m.role == "system"]
        logger.debug(
            f"llm sysetm msg: {system_msgs[0] if system_msgs else 'NA'}\nllm user msg: {messages[-1]}\nllm response: {message}"
        )

        if message.tool_calls:
            for tool_call in message.tool_calls:
                if hasattr(tool_call, "function") and hasattr(
                    tool_call.function, "arguments"
                ):
                    try:
                        tool_call.function.arguments = json.loads(
                            tool_call.function.arguments
                        )
                    except json.JSONDecodeError as e:
                        if strict:
                            raise ValueError(
                                f"Failed to parse tool arguments as JSON: {e}"
                            )
            return message.tool_calls

        if parser and message.content:
            try:
                return parser(message.content)
            except Exception:
                if strict:
                    raise

        return message.content

    async def classify_message(
        self,
        text: str,
        context: Optional[str] = None,
        flow: Optional[Flow] = None,
        language: Language = Language.ENGLISH,
        **kwargs: Any,
    ) -> MessageClassification:
        """Classifies the type of the input message using the LLM."""
        if not text:
            return MessageClassification.NONE

        input_content = context + "\n\n" if context else ""
        input_content += text
        messages = [
            Message(
                role="system",
                content=self.settings.custom_msg_classification_prompt
                or MSG_CLASSIFICATION.to_str(flow, language),
            ),
            Message(
                role="user", content=f"[INPUT]\n{input_content}\n\n[/INPUT]\n[OUTPUT]\n"
            ),
        ]

        try:
            llm_response: str = cast(
                str, await self.generate_response(messages=messages, **kwargs)
            )
            logger.debug(f"llm response:\n{(llm_response)}")

        except Exception as e:
            logger.exception(e)
            return MessageClassification.NONE

        return MessageClassification(llm_response.strip())

    @retry(msg_arg="retry_message")
    async def extract_relation(
        self,
        /,  # mark 'self' as positional-only
        text: str,
        indexed_metadata: IndexedMetadata,
        context: Optional[str] = None,
        flow: Optional[Flow] = None,
        language: Language = Language.ENGLISH,
        retry_message: Optional[str] = None,
        min_chars: int = 32,
        **kwargs: Any,
    ) -> Optional[Relation]:
        """
        Extracts a Relation object from the given text using the LLM.

        This involves generating a summary and then extracting entities and their relationships.
        """

        if len(text) < min_chars:
            return None

        input_content = context + "\n\n" if context else ""
        input_content += text

        try:
            messages = [
                Message(
                    role="system",
                    content=self.settings.custom_summary_prompt
                    or SUMMARY.to_str(flow, language),
                ),
                Message(
                    role="user",
                    content=f"[INPUT]\n{input_content}\n\n[/INPUT]\n[OUTPUT]\n",
                ),
            ]

            summary = cast(
                str,
                await self.generate_response(
                    messages=messages,
                    retry_message=retry_message,
                    max_tokens=4096,
                    **kwargs,
                ),
            )
            logger.debug(f"llm response:\n{(summary)}")

            messages = [
                Message(
                    role="system",
                    content=self.settings.custom_fact_entity_prompt
                    or FACT_ENTITY.to_str(flow, language),
                ),
                Message(
                    role="user",
                    content=f"[INPUT]\n{input_content}\n\n[/INPUT]\n[OUTPUT]\n",
                ),
            ]
            relation = cast(
                Relation,
                await self.generate_response(
                    messages=messages,
                    parser=partial(
                        markdown_to_relation,
                        indexed_metadata=indexed_metadata,
                        chunk_content=text,
                        min_chars=min_chars,
                        summary=summary,
                    ),
                    strict=True,
                    retry_message=retry_message,
                    max_tokens=4096,
                    **kwargs,
                ),
            )
            logger.debug(f"llm response:\n{(relation)}")

        except Exception as e:
            logger.exception(e)
            return None

        return relation
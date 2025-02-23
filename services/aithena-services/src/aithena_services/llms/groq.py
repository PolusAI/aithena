# mypy: disable-error-code="import-untyped"
"""Groq - OpenAI Implementation based on LlamaIndex."""

# pylint: disable=too-many-ancestors, W1203
from typing import Any, Sequence

from aithena_services.config import GROQ_API_KEY, TIMEOUT
from aithena_services.llms.types import Message
from aithena_services.llms.types.base import AithenaLLM, chataithena, streamchataithena
from aithena_services.llms.types.response import (
    ChatResponse,
    ChatResponseAsyncGen,
    ChatResponseGen,
)
from aithena_services.llms.utils import check_and_cast_messages
from llama_index.llms.groq import Groq as LlamaIndexGroq
from groq import Groq as GroqClient  # type: ignore
from polus.aithena.common.logger import get_logger

logger = get_logger("aithena_services.llms.groq")


def list_groq_models() -> list:
    """List available Groq models."""
    if GROQ_API_KEY is None:
        logger.debug("GROQ_API_KEY not set. listing Groq models, returning empty list.")
        return []
    return sorted(
        [x.id for x in GroqClient().models.list().data],
        reverse=True,
    )


class Groq(LlamaIndexGroq, AithenaLLM):
    """Groq models."""

    def __init__(self, timeout=TIMEOUT, **kwargs: Any):
        logger.debug(f"Initializing Groq chat with kwargs: {kwargs}")
        super().__init__(timeout=timeout, **kwargs)

    @staticmethod
    def list_models() -> list:
        """List available Groq chat models."""
        logger.debug(f"Listing Groq chat models")
        return list_groq_models()

    @chataithena
    def chat(self, messages: Sequence[dict | Message], **kwargs: Any) -> ChatResponse:
        """Chat with a model in Groq.

        Args:
            messages: entire list of message history, where last
                message is the one to be responded to
        """
        return super().chat(messages, **kwargs)  # type: ignore

    @streamchataithena
    def stream_chat(
        self, messages: Sequence[dict | Message], **kwargs: Any
    ) -> ChatResponseGen:
        """Stream chat with a model in Groq.

        Each response is a `ChatResponse` and has a `.delta`
        attribute useful for incremental updates.

        Args:
            messages: entire list of message history, where last
                message is the one to be responded to
        """
        return super().stream_chat(messages, **kwargs)  # type: ignore

    async def achat(
        self, messages: Sequence[dict | Message], **kwargs: Any
    ) -> ChatResponse:
        """Async chat with a model in Groq.

        Args:
            messages: entire list of message history, where last
                message is the one to be responded to
        """
        messages_ = check_and_cast_messages(messages)
        llama_index_response = await super().achat(messages_, **kwargs)
        return ChatResponse.from_llamaindex(llama_index_response)

    async def astream_chat(
        self, messages: Sequence[dict | Message], **kwargs: Any
    ) -> ChatResponseAsyncGen:
        """Async stream chat with a model in Groq.

        Each response is a `ChatResponse` and has a `.delta`
        attribute useful for incremental updates.

        Args:
            messages: entire list of message history, where last
                message is the one to be responded to
        """
        messages = check_and_cast_messages(messages)
        llama_stream = super().astream_chat(messages, **kwargs)

        async def gen() -> ChatResponseAsyncGen:
            async for response in await llama_stream:
                yield ChatResponse.from_llamaindex(response)

        return gen()

# mypy: disable-error-code="import-untyped"
"""Ollama implementation based on LlamaIndex."""

# pylint: disable=too-many-ancestors, W1203
import logging
from typing import Any, Sequence

import requests  # type: ignore
from llama_index.llms.ollama import Ollama as LlamaIndexOllama  # type: ignore

from aithena_services.envvars import OLLAMA_HOST
from aithena_services.llms.types import Message
from aithena_services.llms.types.base import AithenaLLM, chataithena, streamchataithena
from aithena_services.llms.types.response import (
    ChatResponse,
    ChatResponseAsyncGen,
    ChatResponseGen,
)
from aithena_services.llms.utils import check_and_cast_messages

logger = logging.getLogger("aithena_services.llms.ollama")


# TODO: check how to set multiple stop sequences, because Ollama supports it
class Ollama(LlamaIndexOllama, AithenaLLM):
    """Ollama LLMs.

    To use this, you must first deploy a model on Ollama.

    You must have the following environment variables set:

    OLLAMA_HOST: url for the Ollama server, e.g.
       http://localhost:11434

    Args:
        model: name of the model (e.g. `llama3.1`)
        request_timeout: timeout for the request in seconds, default is 30
        temperature: temperature for sampling, higher values => more creative answers

            0 ≤ temperature ≤ 1.0

        context_window: maximum number of tokens to consider in the context, default is 3900
        ...

    For a full list of parameters, visit
    [Ollama Docs](https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values)

    """

    def __init__(self, **kwargs: Any):
        if "base_url" not in kwargs or kwargs["base_url"] is None:
            kwargs["base_url"] = OLLAMA_HOST
        logger.debug(f"Initalizing Ollama with kwargs: {kwargs}")
        super().__init__(**kwargs)

    @staticmethod
    def list_models(url: str = OLLAMA_HOST) -> list[str]:  # type: ignore
        """List available Ollama models."""
        r = [
            x["name"]
            for x in requests.get(url + "/api/tags", timeout=40).json()["models"]
        ]
        return [x for x in r if "embed" not in x]

    @chataithena
    def chat(self, messages: Sequence[dict | Message], **kwargs: Any) -> ChatResponse:
        """Chat with a model in Ollama.

        Args:
            messages: entire list of message history, where last
                message is the one to be responded to
        """
        return super().chat(messages, **kwargs)  # type: ignore

    @streamchataithena
    def stream_chat(
        self, messages: Sequence[dict | Message], **kwargs: Any
    ) -> ChatResponseGen:
        """Stream chat with a model in Ollama.

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
        """Async chat with a model in Ollama.

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
        """Async stream chat with a model in Azure OpenAI.

        Each response is a `ChatResponse` and has a `.delta`
        attribute useful for incremental updates.

        Args:
            messages: entire list of message history, where last
                message is the one to be responded to
        """
        messages_ = check_and_cast_messages(messages)
        llama_stream = super().astream_chat(messages_, **kwargs)

        async def gen() -> ChatResponseAsyncGen:
            async for response in await llama_stream:
                yield ChatResponse.from_llamaindex(response)

        return gen()

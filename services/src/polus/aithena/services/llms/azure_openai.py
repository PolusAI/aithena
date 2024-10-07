# mypy: disable-error-code="import-untyped"
"""Ollama implementation based on LlamaIndex."""

# pylint: disable=too-many-ancestors
from typing import Any, Sequence

from llama_index.llms.azure_openai import AzureOpenAI as LlamaIndexAzureOpenAI

from aithena_services.common.azure import resolve_azure_deployment
from aithena_services.envvars import (
    AZURE_OPENAI_CHAT_MODELS_DICT,
    AZURE_OPENAI_ENV_DICT,
)
from aithena_services.llms.types import Message
from aithena_services.llms.types.base import AithenaLLM, chataithena, streamchataithena
from aithena_services.llms.types.response import (
    ChatResponse,
    ChatResponseAsyncGen,
    ChatResponseGen,
)
from aithena_services.llms.utils import check_and_cast_messages


class AzureOpenAI(LlamaIndexAzureOpenAI, AithenaLLM):
    """Azure OpenAI LLMs.

    To use this, you must first deploy a model on Azure OpenAI.
    Unlike OpenAI, you need to specify a `engine` parameter to identify
    your deployment (called "model deployment name" in Azure portal).
    You must have the following environment variables set:

    - `AZURE_OPENAI_API_VERSION`: set this to `2023-07-01-preview` or newer.
        This may change in the future.
    - `AZURE_OPENAI_ENDPOINT`: your endpoint should look like the following
        https://YOUR_RESOURCE_NAME.openai.azure.com/
    - `AZURE_OPENAI_API_KEY`: your API key

    Args:
        model: Name of the model (e.g. `gpt-4o-mini`)
        deployment: This will correspond to the custom name you chose
            for your deployment when you deployed a model.
            Alias: `engine`.

    """

    @staticmethod
    def list_deployments() -> list[str]:
        """List available deployments in Azure OpenAI.

        This method lists all available deployments for Azure OpenAI
        that are listed as environment variables in the correct format.
        The format is `AZURE_OPENAI_DEPLOYMENT_CHAT_{name}={value}`.
        """
        return list(AZURE_OPENAI_CHAT_MODELS_DICT.keys())

    list_models = list_deployments  # Alias

    def __init__(self, **kwargs: Any):
        for arg in ["api_key", "azure_endpoint", "api_version"]:
            if arg not in kwargs or kwargs[arg] is None:
                kwargs[arg] = AZURE_OPENAI_ENV_DICT[arg]
        if "deployment" in kwargs:
            if "engine" in kwargs:
                raise ValueError("Cannot specify both `deployment` and `engine`.")
            kwargs["engine"] = kwargs.pop("deployment")
        kwargs["engine"] = resolve_azure_deployment(
            kwargs["engine"], AZURE_OPENAI_CHAT_MODELS_DICT
        )
        super().__init__(**kwargs)

    @chataithena
    def chat(self, messages: Sequence[dict | Message], **kwargs: Any) -> ChatResponse:
        """Chat with a model in Azure OpenAI.

        Args:
            messages: entire list of message history, where last
                message is the one to be responded to
        """
        return super().chat(messages, **kwargs)  # type: ignore

    @streamchataithena
    def stream_chat(
        self, messages: Sequence[dict | Message], **kwargs: Any
    ) -> ChatResponseGen:
        """Stream chat with a model in Azure OpenAI.

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
        """Async chat with a model in Azure OpenAI.

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

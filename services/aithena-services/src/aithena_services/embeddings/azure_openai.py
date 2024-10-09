# pylint: disable=R0901
# mypy: disable-error-code="import-untyped"
"""Azure OpenAI Embeddings based on LlamaIndex."""

from typing import Optional

from llama_index.embeddings.azure_openai import (
    AzureOpenAIEmbedding as LlamaIndexAzureOpenAI,
)

from aithena_services.common.azure import resolve_azure_deployment
from aithena_services.envvars import (
    AZURE_OPENAI_EMBED_MODELS_DICT,
    AZURE_OPENAI_ENV_DICT,
)


class AzureOpenAIEmbedding(LlamaIndexAzureOpenAI):
    """Azure OpenAI embeddings."""

    @staticmethod
    def list_deployments() -> list[str]:
        """List available deployments in Azure OpenAI.

        This method lists all available deployments for Azure OpenAI
        that are listed as environment variables in the correct format.
        The format is `AZURE_OPENAI_DEPLOYMENT_EMBED_{name}={value}`.
        """
        return list(AZURE_OPENAI_EMBED_MODELS_DICT.keys())

    list_models = list_deployments  # Alias

    def __init__(
        self, deployment: Optional[str] = None, **kwargs
    ):  # deployment is alias for azure_deployment
        kwargs["api_key"] = AZURE_OPENAI_ENV_DICT["api_key"]
        kwargs["api_version"] = AZURE_OPENAI_ENV_DICT["api_version"]
        if deployment:
            kwargs.pop("azure_deployment", None)
            kwargs["azure_deployment"] = resolve_azure_deployment(
                deployment, AZURE_OPENAI_EMBED_MODELS_DICT
            )
        super().__init__(**kwargs)

    def aget_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get text embeddings asynchronously."""
        return self._aget_text_embeddings(texts)

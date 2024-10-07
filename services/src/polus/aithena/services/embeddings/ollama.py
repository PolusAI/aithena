# mypy: disable-error-code="import-untyped"
# pylint: disable=too-many-ancestors
"""Ollama Embeddings based on LlamaIndex."""

from typing import Any

import requests  # type: ignore
from llama_index.embeddings.ollama import OllamaEmbedding as LlamaIndexOllama

from aithena_services.envvars import OLLAMA_HOST


class OllamaEmbedding(LlamaIndexOllama):
    """Ollama embeddings."""

    def __init__(self, **kwargs: Any):
        if "model_name" not in kwargs:
            if "model" not in kwargs:
                raise ValueError("Model not specified.")
            kwargs["model_name"] = kwargs["model"]
        if "base_url" not in kwargs or kwargs["base_url"] is None:
            kwargs["base_url"] = OLLAMA_HOST
        super().__init__(**kwargs)

    @staticmethod
    def list_models(url: str = OLLAMA_HOST) -> list[str]:  # type: ignore
        """List available Ollama models."""
        r = [
            x["name"]
            for x in requests.get(url + "/api/tags", timeout=40).json()["models"]
        ]
        return [x for x in r if "embed" in x]

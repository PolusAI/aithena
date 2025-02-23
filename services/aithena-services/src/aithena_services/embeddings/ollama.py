# mypy: disable-error-code="import-untyped"
# pylint: disable=too-many-ancestors, W1203
"""Ollama Embeddings based on LlamaIndex."""

from typing import Any

import requests  # type: ignore
from aithena_services.config import OLLAMA_HOST
from llama_index.embeddings.ollama import OllamaEmbedding as LlamaIndexOllama
from polus.aithena.common.logger import get_logger

logger = get_logger("aithena_services.embeddings.ollama")


class OllamaEmbedding(LlamaIndexOllama):
    """Ollama embeddings."""

    def __init__(self, **kwargs: Any):
        if "model_name" not in kwargs:
            if "model" not in kwargs:
                raise ValueError("Model not specified.")
            kwargs["model_name"] = kwargs["model"]
        if "base_url" not in kwargs or kwargs["base_url"] is None:
            kwargs["base_url"] = OLLAMA_HOST
        logger.debug(f"Initalizing Ollama embedding with kwargs: {kwargs}")
        super().__init__(**kwargs)

    @staticmethod
    # type: ignore
    def list_models(url: str | None = OLLAMA_HOST) -> list:
        """List available Ollama models."""
        if url is None:
            logger.debug(
                "No Ollama url provided, listing embedding models, returning empty list")
            return []
        logger.debug(f"Listing Ollama embedding models at {url}")
        r = [
            x["name"]
            for x in requests.get(url + "/api/tags", timeout=40).json()["models"]
        ]
        return [x for x in r if "embed" in x]

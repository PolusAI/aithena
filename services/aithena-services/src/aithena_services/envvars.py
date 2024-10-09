"""Environment Variable Configuration for Aithena Services."""

import logging
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

env = os.environ

OPENAI_KEY = os.getenv("OPENAI_API_KEY", None)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", None)
if isinstance(OLLAMA_HOST, str) and OLLAMA_HOST.endswith("/"):
    OLLAMA_HOST = OLLAMA_HOST[:-1]

# ----AzureOpenAI----
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY", None)
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", None)
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", None)
AZURE_OPENAI_ENV_DICT = {
    "api_key": AZURE_OPENAI_KEY,
    "azure_endpoint": AZURE_OPENAI_ENDPOINT,  # redundant name, compatible with LI
    "api_version": AZURE_OPENAI_API_VERSION,
}
AZURE_OPENAI_CHAT_MODELS_DICT: dict[str, str] = {}
AZURE_OPENAI_EMBED_MODELS_DICT: dict[str, str] = {}
for key, value in env.items():
    if key.startswith("AZURE_OPENAI_DEPLOYMENT_CHAT"):
        k = key.split("_")[-1].lower()
        AZURE_OPENAI_CHAT_MODELS_DICT[k] = value
    if key.startswith("AZURE_OPENAI_DEPLOYMENT_EMBED"):
        k = key.split("_")[-1].lower()
        AZURE_OPENAI_EMBED_MODELS_DICT[k] = value


__all__ = [
    "OPENAI_KEY",
    "OLLAMA_HOST",
    "AZURE_OPENAI_ENV_DICT",
    "AZURE_OPENAI_CHAT_MODELS_DICT",
    "AZURE_OPENAI_EMBED_MODELS_DICT",
]

logger = logging.getLogger(__name__)
logger.info("Environment variables loaded.")
logger.info(f"OPENAI_KEY: {OPENAI_KEY}")
logger.info(f"OLLAMA_HOST: {OLLAMA_HOST}")
logger.info(f"AZURE_OPENAI_ENV_DICT: {AZURE_OPENAI_ENV_DICT}")
logger.info(f"AZURE_OPENAI_CHAT_MODELS_DICT: {AZURE_OPENAI_CHAT_MODELS_DICT}")
logger.info(f"AZURE_OPENAI_EMBED_MODELS_DICT: {AZURE_OPENAI_EMBED_MODELS_DICT}")

import os

from dotenv import find_dotenv, load_dotenv
from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import time_logger

load_dotenv(find_dotenv(), override=True)

TIMEOUT = int(os.environ.get("TIMEOUT") or "30")
RETRY_AFTER = int(os.environ.get("RETRY_AFTER") or "5")
RETRY_ATTEMPTS = int(os.environ.get("RETRY_ATTEMPTS") or "3")

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


logger = get_logger(__file__)

logger.info(f"""
Aithena-Services started with TIMEOUT: {TIMEOUT}, RETRY_AFTER: {RETRY_AFTER}, RETRY_ATTEMPTS: {RETRY_ATTEMPTS},
OPENAI_KEY: {OPENAI_KEY}, OLLAMA_HOST: {OLLAMA_HOST}, AZURE_OPENAI_ENV: {AZURE_OPENAI_ENV_DICT},
AZURE_OPENAI_CHAT_MODELS: {list(AZURE_OPENAI_CHAT_MODELS_DICT.keys())}, AZURE_OPENAI_EMBED_MODELS: {list(AZURE_OPENAI_EMBED_MODELS_DICT.keys())}
""")


__all__ = [
    "TIMEOUT",
    "RETRY_AFTER",
    "RETRY_ATTEMPTS",
    "OPENAI_KEY",
    "OLLAMA_HOST",
    "AZURE_OPENAI_ENV_DICT",
    "AZURE_OPENAI_CHAT_MODELS_DICT",
    "AZURE_OPENAI_EMBED_MODELS_DICT",
]
"""Configuration for Ask Aithena Agent."""

import logging
from pathlib import Path
from dotenv import load_dotenv
import os

AITHENA_LOG_LEVEL = os.getenv("AITHENA_LOG_LEVEL", "INFO")

load_dotenv(override=True)

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)

# logging
USE_LOGFIRE = os.environ.get("USE_LOGFIRE", default="False").lower() == "true"
LOGFIRE_SERVICE_NAME = os.environ.get(
    "LOGFIRE_SERVICE_NAME", default="ask-aithena-agent"
)
LOGFIRE_SERVICE_VERSION = os.environ.get("LOGFIRE_SERVICE_VERSION", default="1.0.0")

HTTPX_TIMEOUT = int(os.environ.get("HTTPX_TIMEOUT", default=30))

LITELLM_URL = os.environ.get("LITELLM_URL", default="http://localhost:4000/v1")
LITELLM_URL = LITELLM_URL.rstrip("/")
if not LITELLM_URL.endswith("/v1"):
    logger.warning("LITELLM_URL does not end with /v1. Adding it.")
    LITELLM_URL += "/v1"
LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", default="sk-1212")
PROMPTS_DIR = os.environ.get("PROMPTS_DIR", default="./prompts")
PROMPTS_DIR = Path(PROMPTS_DIR).resolve()

RESPONDER_MODEL = os.environ.get("RESPONDER_MODEL", default="gpt-4.1")
RESPONDER_MODEL_FREQUENCY_PENALTY = os.environ.get(
    "RESPONDER_MODEL_FREQUENCY_PENALTY", default=None
)
RESPONDER_MODEL_FREQUENCY_PENALTY = float(RESPONDER_MODEL_FREQUENCY_PENALTY) if RESPONDER_MODEL_FREQUENCY_PENALTY is not None else None
RESPONDER_MODEL_MAX_TOKENS = os.environ.get("RESPONDER_MODEL_MAX_TOKENS", default=None)
RESPONDER_MODEL_MAX_TOKENS = int(RESPONDER_MODEL_MAX_TOKENS) if RESPONDER_MODEL_MAX_TOKENS is not None else None
RESPONDER_MODEL_TOP_P = os.environ.get("RESPONDER_MODEL_TOP_P", default=None)
RESPONDER_MODEL_TOP_P = float(RESPONDER_MODEL_TOP_P) if RESPONDER_MODEL_TOP_P is not None else None
RESPONDER_MODEL_PRESENCE_PENALTY = os.environ.get(
    "RESPONDER_MODEL_PRESENCE_PENALTY", default=None
)
RESPONDER_MODEL_PRESENCE_PENALTY = float(RESPONDER_MODEL_PRESENCE_PENALTY) if RESPONDER_MODEL_PRESENCE_PENALTY is not None else None
RESPONDER_MODEL_SEED = os.environ.get("RESPONDER_MODEL_SEED", default=None)
RESPONDER_MODEL_SEED = int(RESPONDER_MODEL_SEED) if RESPONDER_MODEL_SEED is not None else None
RESPONDER_MODEL_TEMPERATURE = float(os.environ.get("RESPONDER_MODEL_TEMPERATURE", default=0.3))

RESPONDER_MODEL_PARAMS = {
    "frequency_penalty": RESPONDER_MODEL_FREQUENCY_PENALTY,
    "max_tokens": RESPONDER_MODEL_MAX_TOKENS,
    "top_p": RESPONDER_MODEL_TOP_P,
    "presence_penalty": RESPONDER_MODEL_PRESENCE_PENALTY,
    "seed": RESPONDER_MODEL_SEED,
    "temperature": RESPONDER_MODEL_TEMPERATURE,
}
RESPONDER_MODEL_PARAMS = {k: v for k, v in RESPONDER_MODEL_PARAMS.items() if v is not None}

TALKER_MODEL = os.environ.get("TALKER_MODEL", default="gpt-4.1")
TALKER_MODEL_FREQUENCY_PENALTY = os.environ.get(
    "TALKER_MODEL_FREQUENCY_PENALTY", default=None
)
TALKER_MODEL_FREQUENCY_PENALTY = float(TALKER_MODEL_FREQUENCY_PENALTY) if TALKER_MODEL_FREQUENCY_PENALTY is not None else None
TALKER_MODEL_MAX_TOKENS = os.environ.get("TALKER_MODEL_MAX_TOKENS", default=None)
TALKER_MODEL_MAX_TOKENS = int(TALKER_MODEL_MAX_TOKENS) if TALKER_MODEL_MAX_TOKENS is not None else None
TALKER_MODEL_TOP_P = os.environ.get("TALKER_MODEL_TOP_P", default=None)
TALKER_MODEL_TOP_P = float(TALKER_MODEL_TOP_P) if TALKER_MODEL_TOP_P is not None else None
TALKER_MODEL_PRESENCE_PENALTY = os.environ.get(
    "TALKER_MODEL_PRESENCE_PENALTY", default=None
)
TALKER_MODEL_PRESENCE_PENALTY = float(TALKER_MODEL_PRESENCE_PENALTY) if TALKER_MODEL_PRESENCE_PENALTY is not None else None
TALKER_MODEL_SEED = os.environ.get("TALKER_MODEL_SEED", default=None)
TALKER_MODEL_SEED = int(TALKER_MODEL_SEED) if TALKER_MODEL_SEED is not None else None
TALKER_MODEL_TEMPERATURE = float(os.environ.get("TALKER_MODEL_TEMPERATURE", default=0.3))

TALKER_MODEL_PARAMS = {
    "frequency_penalty": TALKER_MODEL_FREQUENCY_PENALTY,
    "max_tokens": TALKER_MODEL_MAX_TOKENS,
    "top_p": TALKER_MODEL_TOP_P,
    "presence_penalty": TALKER_MODEL_PRESENCE_PENALTY,
    "seed": TALKER_MODEL_SEED,
    "temperature": TALKER_MODEL_TEMPERATURE,
}
TALKER_MODEL_PARAMS = {k: v for k, v in TALKER_MODEL_PARAMS.items() if v is not None}

SEMANTICS_MODEL = os.environ.get("SEMANTICS_MODEL", default="mistral-small3.2")
SEMANTICS_TEMPERATURE = float(os.environ.get("SEMANTICS_TEMPERATURE", default=0.2))

SHIELD_MODEL = os.environ.get("SHIELD_MODEL", default="o4-mini")
SHIELD_TEMPERATURE = float(os.environ.get("SHIELD_TEMPERATURE", default=0.2))

AEGIS_ORCHESTRATOR_MODEL = os.environ.get("AEGIS_ORCHESTRATOR_MODEL", default="o4-mini")
AEGIS_ORCHESTRATOR_TEMPERATURE = float(os.environ.get("AEGIS_ORCHESTRATOR_TEMPERATURE", default=0.2))
AEGIS_REFEREE_MODEL = os.environ.get("AEGIS_REFEREE_MODEL", default="o3")
AEGIS_REFEREE_TEMPERATURE = float(os.environ.get("AEGIS_REFEREE_TEMPERATURE", default=0.3))

ARCTIC_HOST = os.environ.get("ARCTIC_HOST", default="localhost")
ARCTIC_PORT = os.environ.get("ARCTIC_PORT", default=8000)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", default="/root/.cache/huggingface/hub/models--Snowflake--snowflake-arctic-embed-l-v2.0/snapshots/dcf86e284785c825570c5fd512ddd682b386fa3d")
EMBEDDING_TABLE = os.environ.get("EMBEDDING_TABLE", default="openalex.abstract_embeddings_arctic")
SIMILARITY_N = int(os.environ.get("SIMILARITY_N", default=10))

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", default="amqp://guest:guest@localhost:5672/")

# Consolidate configuration logging into a single structured log entry
config_values = {
    "litellm_url": LITELLM_URL,
    "litellm_api_key": LITELLM_API_KEY,
    "responder_model": RESPONDER_MODEL,
    "responder_model_params": RESPONDER_MODEL_PARAMS,
    "talker_model": TALKER_MODEL,
    "talker_model_params": TALKER_MODEL_PARAMS,
    "arctic_host": ARCTIC_HOST,
    "arctic_port": ARCTIC_PORT,
    "embedding_model": EMBEDDING_MODEL,
    "embedding_table": EMBEDDING_TABLE,
    "similarity_n": SIMILARITY_N,
    "aegis_orchestrator_model": AEGIS_ORCHESTRATOR_MODEL,
    "aegis_orchestrator_temperature": AEGIS_ORCHESTRATOR_TEMPERATURE,
    "aegis_referee_model": AEGIS_REFEREE_MODEL,
    "aegis_referee_temperature": AEGIS_REFEREE_TEMPERATURE,
    "shield_model": SHIELD_MODEL,
    "shield_temperature": SHIELD_TEMPERATURE,
    "semantics_model": SEMANTICS_MODEL,
    "semantics_temperature": SEMANTICS_TEMPERATURE,
    "prompts_dir": PROMPTS_DIR,
    "rabbitmq_url": RABBITMQ_URL,
    "use_logfire": USE_LOGFIRE,
}
logger.debug("Configuration values: %s", config_values)

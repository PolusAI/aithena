"""Contains all startup configuration constants."""
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from polus.aithena.common.utils import init_dir
from polus.aithena.common.logger import get_logger

load_dotenv(find_dotenv(), override=True)
logger = get_logger(__file__)


class MissingEnvVarError(Exception):
    """Raised if a required environment variable is missing."""
    def __init__(self, env_var):
        self.message = f"Missing environment variable: {env_var}"
    def __str__(self):
        return self.message

PARENT_DIR = Path(__file__).parent.absolute()

"""Top level directory where to save app data."""
_APP_DATA_DIR = os.getenv("APP_DATA_DIR")
if _APP_DATA_DIR is None:
    raise MissingEnvVarError(f"APP_DATA_DIR")
APP_DATA_DIR=Path(_APP_DATA_DIR)

"""Directory where contexts are saved."""
SELECTIONS_DIR = init_dir(APP_DATA_DIR / "selections")

"""Qrant instance"""
db_port = os.getenv("QDRANT_PORT")
if db_port is None:
    raise MissingEnvVarError(f"QDRANT_PORT")
QDRANT_PORT = int(db_port)

QDRANT_HOST = os.getenv("QDRANT_HOST")

"""Instruction for embedding a query for db similarity search."""
QUERY_DB_INSTRUCTION = (
    "Retrieve document that best match ( or answer) the query (or question):"
)

DEFAULT_COLLECTION="nist_abstracts_NV-Embed-v1"

from aithena_services.envvars import (
    AZURE_OPENAI_AVAILABLE,
    OLLAMA_AVAILABLE,
    OPENAI_AVAILABLE,
)




if AZURE_OPENAI_AVAILABLE:

    # TODO Check with Camilo
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", None)
    AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", None)
    from aithena_services.llms.azure_openai import AzureOpenAI
if OPENAI_AVAILABLE:
    from aithena_services.llms.openai import OpenAI
if OLLAMA_AVAILABLE:
    from aithena_services.llms.ollama import Ollama

from llama_index.core.llms.llm import LLM


# keep track of all available models
LLMS_AVAILABLE = []
if AZURE_OPENAI_AVAILABLE:
    LLMS_AVAILABLE.append(f"azure/{AZURE_OPENAI_MODEL}")
if OPENAI_AVAILABLE:
    LLMS_AVAILABLE.extend(OpenAI.list_models())
if OLLAMA_AVAILABLE:
    LLMS_AVAILABLE.extend(Ollama.list_models())

if len(LLMS_AVAILABLE) == 0:
    raise Exception(f"No models found. Make sure appropriate environment variables are defined.")
logger.info(f"models available: {LLMS_AVAILABLE}")

def create_llm(name: str):
    """Create a model client for a given model configuration
    Configuration are defined through environment variables in aithena services.
    ."""
    if AZURE_OPENAI_AVAILABLE and name.startswith("azure/"):
        return AzureOpenAI(model=AZURE_OPENAI_DEPLOYMENT, deployment=AZURE_OPENAI_DEPLOYMENT)
    if OPENAI_AVAILABLE and name in OpenAI.list_models():
        return OpenAI(model=name)
    if OLLAMA_AVAILABLE and name in Ollama.list_models():
        return Ollama(model=name)


"""Retrieve all available models.
TODO this should probably be part of the services API
since aithena-services act as a gateway to all models.
"""
LLM_DICT = {name: create_llm(name) for name in LLMS_AVAILABLE}

logger.info(f"llm created: {LLM_DICT}")

# TODO remove when done testings
SUMMARY_CUTOFF = 40


os.environ.setdefault("OLLAMA_SERVICE_URL", "http://localhost:30434")
OLLAMA_SERVICE_URL=os.environ.get("OLLAMA_SERVICE_URL")
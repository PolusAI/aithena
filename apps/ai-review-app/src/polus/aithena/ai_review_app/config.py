"""Contains all startup configuration constants."""
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from polus.aithena.common.logger import get_logger

load_dotenv(find_dotenv())
logger = get_logger(__file__)

class MissingEnvVarError(Exception):
    """Raised if a required environment variable is missing."""
    def __init__(self, env_var):
        self.message = f"Missing environment variable: {env_var}"
    def __str__(self):
        return self.message

"""Top level directory where to save app data."""
_APP_DATA_DIR = os.getenv("APP_DATA_DIR", None)
if _APP_DATA_DIR is None:
    raise MissingEnvVarError(f"APP_DATA_DIR")
APP_DATA_DIR=Path(_APP_DATA_DIR)
logger.debug(f"APP_DATA_DIR: {_APP_DATA_DIR}")

"""Qrant instance"""
db_port = os.getenv("QDRANT_PORT", None)
if db_port is None:
    raise MissingEnvVarError(f"QDRANT_PORT")
QDRANT_PORT = int(db_port)
QDRANT_HOST = os.getenv("QDRANT_HOST", None)
if QDRANT_HOST is None:
    raise MissingEnvVarError(f"QDRANT_HOST")

DEFAULT_COLLECTION=os.getenv("DEFAULT_COLLECTION","nist_abstracts_NV-Embed-v1")

AITHENA_SERVICE_URL=os.environ.get("AITHENA_SERVICE_URL", "http://localhost:8000")
DEFAULT_CHAT_MODEL=os.environ.get("CHAT_MODEL", "llama3.1")


"""For testing. If set to -1, all clusters will be summarized."""
SUMMARY_CUTOFF=int(os.environ.get("SUMMARY_CUTOFF","-1"))
LLM_ROLE="user"
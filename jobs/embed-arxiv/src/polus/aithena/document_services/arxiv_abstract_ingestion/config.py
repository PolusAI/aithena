import os
from pathlib import Path

from dotenv import find_dotenv
from dotenv import load_dotenv
from polus.aithena.common.utils import init_dir

load_dotenv(find_dotenv(), override=True)

os.environ.setdefault("DB_PORT", "6333")
DB_PORT = int(os.environ.get("DB_PORT"))

os.environ.setdefault("DB_HOST", "localhost")
DB_HOST = os.environ.get("DB_HOST")

os.environ.setdefault("DB_ABSTRACT_COLLECTION", "arxiv_abstracts_instructorxl")
DB_ABSTRACT_COLLECTION = os.environ.get("DB_ABSTRACT_COLLECTION")

# TODO this should be a input parameter in the typer cli.
os.environ.setdefault("DATA_DIR", ".")
DATA_DIR = Path(os.environ.get("DATA_DIR"))

# NOTE for now this is how data is stored by the oai-pmh client
DOWNLOAD_DIR = os.environ.setdefault("DOWNLOAD_DIR", "downloads")
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR")
DOWNLOAD_DIR = init_dir(DATA_DIR / DOWNLOAD_DIR)

ARXIV_LIST_RECORDS_DIR = os.environ.setdefault(
    "ARXIV_LIST_RECORDS_DIR", "export.arxiv.org/ListRecords"
)
ARXIV_LIST_RECORDS_DIR = os.environ.get("ARXIV_LIST_RECORDS_DIR")
ARXIV_LIST_RECORDS_DIR = init_dir(DOWNLOAD_DIR / ARXIV_LIST_RECORDS_DIR)

LOG_DIR = init_dir(DATA_DIR / "logs")
ARXIV_INGEST_LOG_DIR = init_dir(LOG_DIR / "arxiv")

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%Y-%m-%d_%H:%M:%S"

os.environ.setdefault(
    "EMBED_INSTRUCTION", "Represent this scientific abstract for retrieval."
)
EMBED_INSTRUCTION = os.environ.get("EMBED_INSTRUCTION")

os.environ.setdefault("BATCH_SIZE", "10")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE"))

os.environ.setdefault("EMBED_MODEL_BATCH_SIZE", "5")
EMBED_MODEL_BATCH_SIZE = int(os.environ.get("EMBED_MODEL_BATCH_SIZE"))

os.environ.setdefault("MAX_WORKERS", "1")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS"))

os.environ.setdefault(
    "EMBED_URL", "http://ollama-service.default.svc.cluster.local:11434/api/embed"
)
EMBED_URL = os.environ.get("EMBED_URL")

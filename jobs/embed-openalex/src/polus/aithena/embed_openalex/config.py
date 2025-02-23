import os
from polus.aithena.common.logger import get_logger
from dotenv import load_dotenv

# Configure logging
logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Control how to process the data
CUTOFF = int(os.getenv("CUTOFF", "-1"))
OFFSET = int(os.getenv("OFFSET", "0"))
WORKERS_COUNT = int(os.getenv("WORKERS_COUNT", "-1"))

# Get database connection parameters from environment variables
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
DB_MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "64"))
DB_FORCE_UPDATE = os.getenv("DB_FORCE_UPDATE", "True").lower() == "true"
DB_CONN_TIMEOUT = 300
CONN_INFO = (
    f"host={POSTGRES_HOST} "
    + f"port={POSTGRES_PORT} "
    + f"dbname={POSTGRES_DB} "
    + f"user={POSTGRES_USER} "
    + f"password={POSTGRES_PASSWORD}"
)
logger.info(f"Connecting to database {POSTGRES_DB} on {POSTGRES_HOST}:{POSTGRES_PORT} as user {POSTGRES_USER}")

# Embed Config
# If set, use this host for all workers, else auto-detect.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost") 
 # if OLLAMA_HOST, this should be the nodeport
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "32437"))
# OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_HTTP_TIMEOUT = 30
DEFAULT_HEADERS = { "Content-Type": "application/json"}
SEARCH_DOC_PREFIX="search_document:"
# TODO CHECK should be the same as ollama queue
EMBED_MAX_CONCURRENT_REQUESTS = int(os.getenv("EMBED_MAX_CONCURRENT_REQUESTS", "200"))
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "100"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_SIZE = os.getenv("EMBEDDING_SIZE","768")
# name of the table where embeddings are stored
EMBEDDING_TABLE = f"{EMBEDDING_MODEL.replace('-','_')}_{EMBEDDING_SIZE}"
AVG_TEXT_TOKENS_COUNT = int(512) # Longer texts will be truncated for embedding
CONTEXT_WINDOW_SIZE = AVG_TEXT_TOKENS_COUNT * EMBED_BATCH_SIZE
EMBEDDING_OPTIONS = {"num_ctx": CONTEXT_WINDOW_SIZE}
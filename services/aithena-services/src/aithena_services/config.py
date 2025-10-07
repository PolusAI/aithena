import os
import logging

from dotenv import find_dotenv, load_dotenv

AITHENA_LOG_LEVEL = os.getenv("AITHENA_LOG_LEVEL", "INFO")

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)

load_dotenv(find_dotenv(), override=True)
logger.info(f"Loaded environment variables from {find_dotenv()}")


# ----Memory----
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")
IVFFLAT_PROBES = os.environ.get("IVFFLAT_PROBES", "44")


logger.info(
    f"""
Aithena-Services started with 
POSTGRES_HOST: {POSTGRES_HOST}, POSTGRES_PORT: {POSTGRES_PORT}, POSTGRES_USER: {POSTGRES_USER}, POSTGRES_PASSWORD: {"*" * len(POSTGRES_PASSWORD)},
POSTGRES_DB: {POSTGRES_DB}, IVFFLAT_PROBES: {IVFFLAT_PROBES}
"""
)


__all__ = [
    "IVFFLAT_PROBES",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "AITHENA_LOG_LEVEL",
]

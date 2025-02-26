import os

from dotenv import find_dotenv, load_dotenv
from polus.aithena.common.logger import get_logger

load_dotenv(find_dotenv(), override=True)

env = os.environ


# ----Memory----
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")


logger = get_logger(__file__)

logger.info(
    f"""
Aithena-Services started with 
POSTGRES_HOST: {POSTGRES_HOST}, POSTGRES_PORT: {POSTGRES_PORT}, POSTGRES_USER: {POSTGRES_USER}, POSTGRES_PASSWORD: {POSTGRES_PASSWORD},
POSTGRES_DB: {POSTGRES_DB}
"""
)


__all__ = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
]

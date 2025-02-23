"""Tests configuration and fixtures."""

import pytest
from dotenv import load_dotenv
import os
import psycopg
from polus.aithena.common.logger import get_logger

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get database connection parameters from environment variables
dbname = os.getenv("POSTGRES_DB")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")

logger.info(f"Connecting to database {dbname} on {host}:{port} as user {user}")

@pytest.fixture(scope="module")
def db_connection():
    # Connect to your PostgreSQL database
    conn = psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    yield conn
    conn.close()

def pytest_addoption(parser: pytest.Parser) -> None:
    """Add options to pytest."""
    parser.addoption(
        "--slow",
        action="store_true",
        dest="slow",
        default=False,
        help="run slow tests",
    )


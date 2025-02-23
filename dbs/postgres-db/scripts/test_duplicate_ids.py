""" Integrity test.

Before creating a unique index on the id column of the works table, 
we need to check if there are any duplicate IDs in the table. 
This script will query the database to find any duplicate IDs in the works table.
"""

from dotenv import load_dotenv
import os
import orjson
from polus.aithena.common.utils import time_logger
import psycopg
from polus.aithena.common.logger import get_logger
from openalex_types.works import Work, _construct_abstract_from_index
import requests

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

    # Close the connection
    logger.debug("!!!!!!!!! Closing database connection")
    conn.close()

AITHENA_SERVICES_URL = os.getenv("AITHENA_SERVICES_URL", "http://localhost:8000")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBED_URL = f"{AITHENA_SERVICES_URL}/embed/{EMBEDDING_MODEL}/generate"
DEFAULT_HEADERS = { "Content-Type": "application/json"}

@time_logger
def run_query():
    schema_name = "openalex"
    table_name = "works"

    conn = next(db_connection())
    cur = conn.cursor()

    # Execute the query to get the column names
    cur.execute(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        AND table_schema = '{schema_name}';
    """)

    # Fetch all results
    columns = cur.fetchall()

    logger.debug(f"""{len(columns)} columns found in the {table_name} table""")

    # Print the list of column names
    for column in columns:
        print(column[0])

    # # Execute the query to get the first 10 records from the openalex.works table
    cur.execute(f"""
        SELECT id, COUNT(*)
        FROM {schema_name}.{table_name}
        GROUP BY id
        HAVING COUNT(*) > 1;
    """)

    # Fetch all results
    records = cur.fetchall()
    if len(records) == 0:
        logger.info("No duplicate IDs found")

    for record in records:
        logger.debug(f"duplicate record (id, count): {record}")


def explain_query():
    schema_name = "openalex"
    table_name = "works"

    conn = next(db_connection())
    cur = conn.cursor()

    # Execute the query to get the first 10 records from the openalex.works table
    cur.execute(f"""
        EXPLAIN ANALYZE
        SELECT id, COUNT(*)
        FROM {schema_name}.{table_name}
        GROUP BY id
        LIMIT 10;
    """)

    # Fetch and print the query plan
    query_plan = cur.fetchall()
    for line in query_plan:
        print(line)

if __name__ == "__main__":
    run_query()
    # explain_query()
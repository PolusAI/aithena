""" Integrity test.

Before creating a unique index on the id column of the works table, 
we need to check if there are any duplicate IDs in the table. 
This script will query the database to find any duplicate IDs in the works table.
"""

from dotenv import load_dotenv
import os
from polus.aithena.common.utils import time_logger
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

def db_connection():
    conn = psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    yield conn
    conn.close()

@time_logger
def test_duplicate_ids(schema_name="openalex", table_name="works"):

    conn = next(db_connection())
    cur = conn.cursor()

    cur.execute(f"""
        SELECT id, COUNT(*)
        FROM {schema_name}.{table_name}
        GROUP BY id
        HAVING COUNT(*) > 1;
    """)

    # Fetch all results
    records = cur.fetchall()
    if len(records) == 0:
        logger.info("No duplicate IDs found for schema: {schema_name}, table: {table_name}")
    else:

        for record in records:
            logger.debug(f"duplicate record (id, count): {record}")
        
        raise Exception("Duplicate IDs found for schema: {schema_name}, table: {table_name}")
    
if __name__ == "__main__":
    test_duplicate_ids(schema_name = "openalex", table_name = "works")
from dotenv import load_dotenv
import os
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

def test_table_existence(db_connection):
    # Create a cursor object
    cur = db_connection.cursor()

    # Execute the query to get all tables
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
        AND table_schema NOT IN ('information_schema', 'pg_catalog');
    """)

    # Fetch all results
    tables = cur.fetchall()

    # Print the list of tables
    for table in tables:
        logger.info(f"Schema: {table[0]}, Table: {table[1]}")

    # Close the cursor
    cur.close()

    # Assert that there are tables in the database
    assert len(tables) > 0, "No tables found in the database"
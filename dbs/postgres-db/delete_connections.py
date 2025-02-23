import psycopg
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

# Connect to your PostgreSQL database
conn = psycopg.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)

logger.info(f"Connected to database {dbname} on {host}:{port} as user {user}")

# Create a cursor object
cur = conn.cursor()

# Identify all connections to the database
cur.execute("""
    SELECT pid
    FROM pg_stat_activity
    WHERE datname = %s
    AND pid <> pg_backend_pid();
""", (dbname,))
connections = cur.fetchall()

# Terminate all connections
for pid in connections:
    logger.info(f"Terminating connection {pid[0]}")
    cur.execute(f"SELECT pg_terminate_backend({pid[0]});")

# Commit the transaction
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()
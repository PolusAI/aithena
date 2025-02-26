"""DEPRECATED. First attempt to embed abstracts from OpenAlex database using Aithena services."""
from dotenv import load_dotenv
import os
import orjson
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

def embed(batch_index, texts: list[str]) -> list[float]:
    """Get abstract embedding through Aithena services."""
    response = requests.post(EMBED_URL, headers=DEFAULT_HEADERS, json=texts)
    if response.status_code != 200:
        raise ValueError(f"Failed to get embedding: {response.text}")
    logger.info(response.json())
    return batch_index, response.json()


if __name__ == "__main__":

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
        SELECT *
        FROM {schema_name}.{table_name}
        LIMIT 10;
    """)

    # Fetch all results
    records = cur.fetchall()

    batch_index = 0
    updated_records = {}
    texts = []

    # Turn record tuples to dictionaries
    records_dict = [{str(k[0]): v for k, v in zip(columns, record)} for record in records]
    updated_records[batch_index] = records_dict
    
    # Build abstracts
    for record_dict in records_dict:
        logger.info(record_dict["abstract_inverted_index"])
        if record_dict["abstract_inverted_index"]:
            text = _construct_abstract_from_index(record_dict["abstract_inverted_index"])
        else:
            text = ""
        texts.append(text)
    
    # Embed abstracts
    batch_index, embeddings = embed(batch_index, texts)
    logger.info(f"embedding received...")
    
    # Find batch
    batch = updated_records[batch_index]

    # Add embeddings to records
    for index, record in enumerate(batch):
        record["abstract_embedding"] = embeddings[index]
        # logger.info(record)

    # Persist to database
    for record in batch:
        if not record["abstract_embedding"]:
            continue
        cur.execute(f"""
            INSERT INTO {schema_name}.embeddings_nomic_embed_text_768 (embedding, work_id)
            VALUES (%s, %s)
            RETURNING work_id;
            """, (record["abstract_embedding"], record["id"])
        )

        embedding_id = cur.fetchone()[0]
        logger.info(embedding_id)

        cur.execute(f"""
            UPDATE {schema_name}.{table_name}
            SET abstract_embedding_id = %s
            WHERE id = %s;
        """, (embedding_id, record["id"]))

    batch_index += 1

    cur.execute(f"""
        SELECT *
        FROM {schema_name}.embeddings_nomic_embed_text_768
    """)

    embedding_id = cur.fetchone()[0]
    logger.info(embedding_id)


    cur.close()

    conn.commit()

    logger.debug("!!!!!!!!! Closing database connection")
    logger.debug(f"insert into {schema_name}.embeddings_nomic_embed_text_768 at port {port}")
    conn.close()
    

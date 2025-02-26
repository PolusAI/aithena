"""DEPRECATED. First version of the async embedding script for OpenAlex works."""

from pathlib import Path
from dotenv import load_dotenv
import os
import httpx
from polus.aithena.common.utils import async_time_logger
from polus.aithena.common.logger import get_logger
from openalex_types.works import Work, _construct_abstract_from_index
import psycopg_pool
import asyncio
from tqdm.asyncio import tqdm

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

AITHENA_SERVICES_URL = os.getenv("AITHENA_SERVICES_URL", "http://localhost:8282")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBED_URL = f"{AITHENA_SERVICES_URL}/embed/{EMBEDDING_MODEL}/generate"
EMBEDDING_SIZE = os.getenv("EMBEDDING_SIZE")
EMBEDDING_TABLE = f"embedding_{EMBEDDING_MODEL}_{EMBEDDING_SIZE}"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
CUTOFF = int(os.getenv("CUTOFF", "0"))
OFFSET = int(os.getenv("OFFSET", "0"))
DB_MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "10"))

CONN_INFO = (
    f"host={host} "
    + f"port={port} "
    + f"dbname={dbname} "
    + f"user={user} "
    + f"password={password}"
)

DEFAULT_HEADERS = { "Content-Type": "application/json"}

async def get_async_pool(db_max_connections: int) -> psycopg_pool.ConnectionPool:
    """Get a connection pool for async operations."""
    return psycopg_pool.AsyncConnectionPool(
        CONN_INFO,
        open=False,
        max_size=db_max_connections,
    )

async def async_query(query: str, pool: psycopg_pool.ConnectionPool):
    """Execute a query asynchronously and return the results."""
    logger.debug("Attempt to create connection")
    async with pool.connection() as conn:
        logger.debug("Connected to database")
        async with conn.cursor() as cur:
            logger.debug("Created cursor")
            await cur.execute(query)
            logger.debug("Executed query")
            results = await cur.fetchall()
            return results
        # TODO CHECK cost
        conn.commit()

def save_count_to_disk(file_path : Path, processed_count : int, total_work_count : int):
    """Save the current processed works count to disk.
    
    Keep track of the progress and can be used as offset to resume the job.
    However since openalex schema use text for work id, we cannot rely on
    sequential work id so this is only useful as long as no updates occur.
    """

    status = f"{processed_count}/{total_work_count}"
    with open(file_path, 'w') as file:
        file.write(status)


@async_time_logger
async def embed(texts: list[str]) -> list[float]:
    """Get embedding through Aithena services.
    
    Args:
        texts: List of texts to embed.
    """
    logger.debug(f"Embedding {len(texts)} texts...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(EMBED_URL, headers=DEFAULT_HEADERS, json=texts, timeout=None)
            response.raise_for_status()
            logger.debug(f"embeddings completed {response.json()}")
            return response.json()
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url!r}.")
        raise ValueError(f"Failed to get embedding: {str(exc)}") from exc
    except httpx.HTTPStatusError as exc:
        logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        raise ValueError(f"Failed to get embedding: {exc.response.text}") from exc
    except httpx.ReadTimeout as exc:
        logger.error(f"Read timeout occurred while requesting {exc.request.url!r}.")
        raise ValueError(f"Failed to get embedding: Read timeout") from exc

def get_abstracts(works : list[Work]) -> list[str]:
    """Get abstracts from works.

    If work has no abstract inverted index, return empty string for that work.
    
    Args:
        works: List of works to get abstracts from.
    """
    abstracts = []
    abstract_count = 0
    for work in works:
        text = ""
        if work.abstract_inverted_index:
            text = _construct_abstract_from_index(work.abstract_inverted_index)
            abstract_count += 1
        abstracts.append(text)
    logger.debug(f" {abstract_count} abstracts found out of {len(works)} works...")
    return abstracts

@async_time_logger
async def add_embeddings(
    pool: psycopg_pool.ConnectionPool,
    works: list[Work],
    embeddings: list[list[float]],
    force_update = False):
    """Insert a batch of embeddings to the database in a single operation."""
    schema_name = "openalex"
    table_name = "embeddings_nomic_embed_text_768"
    on_conflict = "DO NOTHING" if not force_update else "DO UPDATE SET embedding = EXCLUDED.embedding"

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # Filter out empty embeddings
            # Also need to cast values to float since psycopg will interpret some values as int.
            # TODO CHECK psycopg for improved handling
            valid_data = [(list(map(float, embedding)), work.id) for work, embedding in zip(works, embeddings) if embedding]
            if not valid_data:
                return

            values_str = ', '.join(f"(%s, %s)" for _ in valid_data)
            values = [item for sublist in valid_data for item in sublist]

            await cur.execute(f"""
                INSERT INTO {schema_name}.{table_name} (embedding, work_id)
                VALUES {values_str}
                ON CONFLICT (work_id) {on_conflict}
                RETURNING work_id;
            """, values)

            work_ids = await cur.fetchall()
            return work_ids

@async_time_logger
async def add_embeddings_one_by_one(pool, works, embeddings, force_update = False):
    """Insert each embeddings to the database in atomic operations."""
    schema_name = "openalex"
    table_name = "embeddings_nomic_embed_text_768"
    on_conflict = "DO NOTHING" if not force_update else "DO UPDATE SET embedding = EXCLUDED.embedding"
    updated_work_ids = []
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            for work, embedding in zip(works, embeddings):
                if not embedding:
                    continue
                workid = await cur.execute(f"""
                INSERT INTO {schema_name}.{table_name} (embedding, work_id)
                VALUES (%s, %s)
                ON CONFLICT (work_id) {on_conflict}
                RETURNING work_id;
                """, (embedding, work.id)
                )
                work_id = await cur.fetchone()
                updated_work_ids.append(work_id)
                logger.debug(f"Inserted embedding for work {work.id} {workid}")
    return updated_work_ids

async def get_work_count(pool):
    """Get the total amount of works in the database."""
    schema_name = "openalex"
    table_name = "works"
    count_works_query = f"""
        SELECT COUNT(*)
        FROM {schema_name}.{table_name}
    """
    res = await async_query(count_works_query, pool)
    total_work_count = res[0][0]
    logger.debug(f"Total amount of works: {total_work_count}")
    return total_work_count

@async_time_logger
async def embed_pipeline(
    offset: int = OFFSET,
    batch_size:int = BATCH_SIZE,
    cutoff: int = CUTOFF,
    db_max_connections: int = DB_MAX_CONNECTIONS
    
    ):
    """Embed all works in the database."""
    schema_name = "openalex"
    table_name = "works"
    file_path = Path.cwd() / 'embed_count.txt'
    file_path.touch(exist_ok=True)

    works_query = f"""
        SELECT *
        FROM {schema_name}.{table_name}
        LIMIT {batch_size}
    """
    try:
        pool = await get_async_pool(db_max_connections)
        await pool.open()
        logger.debug("Got async pool")
        
        embed_count = 0
        processed_count = 0

        if CUTOFF:
            total_work_count = CUTOFF
        else:
            total_work_count = await get_work_count(pool)

        # Heuristic to determine the acceptable number of concurrent batches at any time.
        # This prevents generating massive amount of connection requests before processing any data.
        total_concurrent_batch_size = batch_size * db_max_connections * 2

        for global_batch_index in range(0, total_work_count, total_concurrent_batch_size):
            tasks = []
            # Process current set of batches.
            for batch_index in range(0, total_concurrent_batch_size, batch_size):
                batch_works_query = f"{works_query} OFFSET {offset}"
                tasks.append(async_query(batch_works_query, pool))
                offset += batch_size
                logger.debug(f"Added task {global_batch_index * total_concurrent_batch_size + batch_index} for offset {offset}")

            progress_bar = tqdm(total=total_work_count, desc=f"{processed_count}/{total_work_count}")

            for task in asyncio.as_completed(tasks):
                batch = await task
                works = [Work.from_sql(work) for work in batch]
                logger.info(f"Processing {len(works)} works...")
                assert len(works) == batch_size, f"Works {len(works)} != Batch size {batch_size}"
                abstracts = get_abstracts(works)
                embeddings = await embed(abstracts)
                assert len(embeddings) == len(abstracts), f"Embeddings {len(embeddings)} != Abstracts {len(abstracts)}"
                assert len(embeddings) == batch_size, f"Embeddings {len(embeddings)} != Batch size {batch_size}"
                logger.debug(f"Processing {len(embeddings)} embeddings...")
                new_embeddings = await add_embeddings(pool, works, embeddings, force_update=True)
                if new_embeddings is not None:
                    logger.debug(f"Added {len(new_embeddings)} embeddings to database...")
                    embed_count += len(new_embeddings)
                processed_count += batch_size
                logger.info(f"Processed {processed_count}/{total_work_count} embeddings, added {embed_count}/{total_work_count}  to database.")
                progress_bar.update(batch_size)
                progress_bar.set_description(f"{processed_count}/{total_work_count}")

                save_count_to_disk(file_path, processed_count, total_work_count)
                
    finally:
        await pool.close()
        logger.debug("Closed pool")
        

if __name__ == "__main__":
    asyncio.run(embed_pipeline(OFFSET, BATCH_SIZE, CUTOFF, DB_MAX_CONNECTIONS))
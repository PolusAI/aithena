"""Script to embed missing records.

TODO complete the script to embed missing records.
For now we are just printing the work ids.

We are not missing any records currently, so this is stub for a maintenance script.
"""
import asyncio
from pathlib import Path

from polus.aithena.embed_openalex.embed import get_docs_by_ids
from polus.aithena.common.logger import get_logger
from polus.aithena.embed_openalex.utils.postgres_tools import get_async_pool
from polus.aithena.embed_openalex.config import (
    EMBED_BATCH_SIZE,
    CONN_INFO, DB_MAX_CONNECTIONS, EMBEDDING_TABLE, DB_FORCE_UPDATE,
    AVG_TEXT_TOKENS_COUNT, CONTEXT_WINDOW_SIZE, OLLAMA_HOST, OLLAMA_PORT
)


DB_CONN_TIMEOUT = 300

logger = get_logger(__name__)

def batch_generator(generator, batch_size):
    """
    Batches the results from a generator in batches of a specified size.

    Args:
        generator (generator): The input generator.
        batch_size (int): The size of each batch.

    Yields:
        list: A batch of results.
    """
    batch = []
    for item in generator:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def get_unembedded_work_ids_from_file(file_path):
    """Get unembedded work ids from a file."""
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                work_id = line.strip('()').split(',')[0]
                yield work_id


async def embed_pipeline(
    file_path,
    batch_size=EMBED_BATCH_SIZE,
    conn_info=CONN_INFO,
    db_max_connections=DB_MAX_CONNECTIONS,
    base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
    force_update=DB_FORCE_UPDATE
):
    """Embed pipeline.
    
    Args:
        conn_info: Database connection info.
        db_max_connections: Maximum number of database connections.
        base_url: Ollama base url.
        force_update: Force update embeddings.
        worker_id: Worker id.
    """

    logger.debug(f"avg txt token count : {AVG_TEXT_TOKENS_COUNT}")
    logger.debug(f"context window size : {CONTEXT_WINDOW_SIZE}")
    logger.debug(f"force update embeddings : {force_update}")
    logger.debug(f"embed url : {base_url}")

    pool = await get_async_pool(conn_info, db_max_connections, timeout=DB_CONN_TIMEOUT)
    await pool.open(wait=True)    

    tasks = []
    for batch_id, ids in enumerate(batch_generator(get_unembedded_work_ids_from_file(file_path), 2)):
        logger.debug(f"Running batch {batch_id}")
        tasks.append(run_pipeline(
            ids,
            pool=pool,
            base_url=base_url,
            force_update=force_update,
            schema_name = "openalex",
            table_name = EMBEDDING_TABLE,
            on_conflict = "DO NOTHING" if not force_update else "DO UPDATE SET embedding = EXCLUDED.embedding"
        ))
        if len(tasks) == batch_size:
            await asyncio.gather(*tasks)
            tasks = []
    logger.info(f"Running {len(tasks)} tasks")
    await asyncio.gather(*tasks)


async def run_pipeline(ids, **kwargs):
    """Run the pipeline for a batch of records.
    
    Args:
        batch: A batch of records.
        pool: Database connection pool.
        base_url: Ollama base url.
        force_update: Force update embeddings.
        schema_name: Database schema name.
        table_name: Database table name.
        on_conflict: Database on conflict clause.
    """
    logger.debug(f"Running pipeline for batch {ids}")
    ids, works, texts = await get_docs_by_ids(ids, kwargs)
    # TODO embed the texts
    logger.debug(f"work id: {ids}")
if __name__ == "__main__":
    file_path= Path('/polus2/gerardinad/projects/aithena/jobs/embed-openalex/logs/missing_records.txt')
    asyncio.run(embed_pipeline(file_path, batch_size=2))
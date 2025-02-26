"""Script to run failed batches.
Failed batches are stored in a file as tuple (start, end).
Make sure the batch size is the same as the one used in the failed batches.
"""
import asyncio
from polus.aithena.common.logger import get_logger
from polus.aithena.embed_openalex.utils.postgres_tools import get_async_pool
from parse_failed_embed import get_unembedded_work_ids_from_file
from polus.aithena.embed_openalex.embed import run_pipeline
from polus.aithena.embed_openalex.config import (
    CONN_INFO, DB_CONN_TIMEOUT, DB_MAX_CONNECTIONS, EMBED_BATCH_SIZE, EMBEDDING_TABLE, DB_FORCE_UPDATE,
    AVG_TEXT_TOKENS_COUNT, CONTEXT_WINDOW_SIZE, OLLAMA_HOST, OLLAMA_PORT
)

logger = get_logger(__name__)

async def embed_pipeline(
    file_path,
    offset=0,
    batch_size=EMBED_BATCH_SIZE,
    conn_info=CONN_INFO,
    db_max_connections=DB_MAX_CONNECTIONS,
    base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
    force_update=DB_FORCE_UPDATE,
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
    for begin, end in get_unembedded_work_ids_from_file(file_path):
        if begin >= offset:
            tasks.append(run_pipeline(
                range(begin, end, end-begin),
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


if __name__ == "__main__":
    file_path = '/polus2/gerardinad/projects/aithena/jobs/embed-openalex/logs/failed_embed.txt'
    offset = 0
    asyncio.run(embed_pipeline(file_path, offset=offset, batch_size=100))
"""Batch embedding pipeline for OpenAlex."""
from functools import partial
import random
from typing import Any, Iterable
import httpx
import asyncio
import tqdm
from openalex_types.works import Work, _construct_abstract_from_index
from polus.aithena.common.utils import async_time_logger
from polus.aithena.common.logger import get_logger
from polus.aithena.embed_openalex.utils.openalex_queries import (
    add_embeddings, get_works_batch, get_works_by_ids, get_works_count
)
from polus.aithena.embed_openalex.utils.postgres_tools import get_async_pool
from polus.aithena.embed_openalex.utils.pipeline import Pipeline, Step

from polus.aithena.embed_openalex.config import (
    DB_CONN_TIMEOUT, DEFAULT_HEADERS, EMBED_MAX_CONCURRENT_REQUESTS, EMBED_BATCH_SIZE, EMBEDDING_MODEL,
    CONN_INFO, DB_MAX_CONNECTIONS, CUTOFF, EMBEDDING_OPTIONS, EMBEDDING_TABLE, OFFSET, DB_FORCE_UPDATE,
    AVG_TEXT_TOKENS_COUNT, CONTEXT_WINDOW_SIZE, OLLAMA_HOST, OLLAMA_HTTP_TIMEOUT, OLLAMA_PORT, SEARCH_DOC_PREFIX
)

logger = get_logger(__name__)

@async_time_logger
async def insert_embeddings(
    data: Any,
    kwargs: dict
):
    """Add embeddings to the database.
    
    Args:
        data: Tuple of batch_id, works, texts, embeddings.
        kwargs: Additional keyword arguments.
            pool: Database connection pool.
            schema_name: Database schema name.
            table_name: Database table name.
            on_conflict: Database on conflict clause.
    """
    batch_id, works, texts, embeddings = data

    logger.debug(f"Inserting {len(embeddings)} embeddings into db...")

    assert len(works) == len(embeddings), f"Expected same number of works and embeddings. Expected: {len(works)}, Got: {len(embeddings)}"
    assert batch_id[1]-batch_id[0] == len(works), f"Expected same number of works and batch size. Expected: {batch_id[1]-batch_id[0]}, Got: {len(works)}"

    pool = kwargs.get('pool')
    schema_name = kwargs.get('schema_name')
    table_name = kwargs.get('table_name')
    on_conflict = kwargs.get('on_conflict')

    new_embeddings_work_ids = await add_embeddings(works, embeddings, pool, schema_name, table_name, on_conflict)

    return batch_id, works, texts, embeddings, new_embeddings_work_ids


@async_time_logger
async def embed(data, kwargs) -> list[float]:
    """Embed with Ollama.

    NOTE: Changing any of the model parameters will trigger a model reload.

    Args:
        texts: List of texts to embed.
        kwargs: Additional keyword arguments.
            base_url: Ollama base url.
    """
    batch_id , works, texts = data
    base_url = kwargs.get('base_url')
    url = f"{base_url}/api/embed"

    logger.debug(f"Embedding {len(texts)} texts at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=DEFAULT_HEADERS,
                json={
                    "model": EMBEDDING_MODEL,
                    "input": texts,
                    "truncate": True,
                    "keep_alive": -1,
                    "options": EMBEDDING_OPTIONS,
                }, timeout=OLLAMA_HTTP_TIMEOUT)
            response.raise_for_status()
            embeddings = response.json()["embeddings"]
            return batch_id, works, texts, embeddings
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
            if len(text.split(" ")) > AVG_TEXT_TOKENS_COUNT:
                logger.warning(f"Abstract word count exceeds average token count: {len(text.split(' '))}. Abtract will be truncated.")
        abstracts.append(text)
    assert len(abstracts) == len(works), "Expected same number of abstracts as works."
    return abstracts


async def get_docs_by_ids(
        ids: list[str],
        kwargs
        ):
    """Get works from database and build abstracts when available.
    
    Args:
        ids: List of work ids to get.
        kwargs: Additional keyword arguments.
            pool: Database connection pool.
    """
    pool = kwargs.get('pool')
    logger.debug(f"Getting works by ids...")
    works = await get_works_by_ids(pool, ids)
    texts = get_abstracts(works)
    texts = [f"{SEARCH_DOC_PREFIX} {t}" for t in texts]
    return ids, works, texts


async def get_docs_by_range(
        batch_id: tuple[int, int],
        kwargs
        ):
    """Get works from database and build abstracts when available."""
    offset = batch_id[0]
    cutoff = batch_id[1] - offset
    pool = kwargs.get('pool')
    logger.debug(f"Getting works from offset {offset} with cutoff {cutoff}...")
    works = await get_works_batch(offset, cutoff, pool)
    texts = get_abstracts(works)
    texts = [f"{SEARCH_DOC_PREFIX} {t}" for t in texts]
    return batch_id, works, texts

fast = (0.000001, 0.1)
    

async def do_nothing(data, kwargs):
    await asyncio.sleep(random.uniform(*fast))
    return data,


async def embed_pipeline(
    batch_size=EMBED_BATCH_SIZE,
    conn_info=CONN_INFO,
    db_max_connections=DB_MAX_CONNECTIONS,
    cutoff= CUTOFF,
    offset=OFFSET,
    base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
    force_update=DB_FORCE_UPDATE,
    worker_id=0,
):
    """Embed pipeline.
    
    Args:
        batch_size: Number of works to process in each batch.
        conn_info: Database connection info.
        db_max_connections: Maximum number of database connections.
        cutoff: Number of works to process.
        offset: Starting offset.
        base_url: Ollama base url.
        force_update: Force update embeddings.
        worker_id: Worker id.
    """

    logger.debug(f"batch size : {batch_size}")
    logger.debug(f"start embedding work at offset : {offset}")
    logger.debug(f"cutoff : {cutoff}")
    logger.debug(f"force update embeddings : {force_update}")
    logger.debug(f"embed url : {base_url}")
    logger.debug(f"avg txt token count : {AVG_TEXT_TOKENS_COUNT}")
    logger.debug(f"context window size : {CONTEXT_WINDOW_SIZE}")

    pool = await get_async_pool(conn_info, db_max_connections, timeout=DB_CONN_TIMEOUT)
    await pool.open(wait=True)

    # figure out how many records to process
    if offset < 0:
        offset = 0
    if cutoff > 0:
        total_works_count = cutoff
    else:
        total_works_count = await get_works_count(pool) - offset
    logger.debug(f"Total works count to process: {total_works_count} for worker {worker_id}")

    await run_pipeline(
        range(offset,offset + total_works_count, batch_size),
        pool=pool,
        base_url=base_url,
        force_update=force_update,
        schema_name = "openalex",
        table_name = EMBEDDING_TABLE,
        on_conflict = "DO NOTHING" if not force_update else "DO UPDATE SET embedding = EXCLUDED.embedding"
    )


def update_res(pbar, res, kwargs):
    """Callback when receiving a new result from the pipeline.

    We log the result and update the progress bar.
    
    Args:
        res: Result from the pipeline.
        kwargs: Additional keyword arguments.
    """
    batch_id, works, texts, _, work_ids = res
    w_abstracts = len([t for t in texts if t != ""])
    logger.info(f"batch {batch_id}, total works: {len(works)} ,abstracts : {w_abstracts}, {len(work_ids)} embeddings inserted.")
    pbar.update(1)


async def run_embed_record_pipeline(data: Iterable, **kwargs: dict):
    """
    Run the embedding pipeline.

    Args:
        data (Iterable): Iterable of data to process.
        **kwargs (dict): Additional keyword arguments for configuration.
            pool (psycopg_pool.ConnectionPool): The database connection pool.
            base_url (str): The base URL for processing.
            force_update (bool): Whether to force update the data.
    """

    pbar = tqdm.tqdm(data)

    # Create steps
    step1  = Step(1, workers_count=DB_MAX_CONNECTIONS // 2, queue_size=DB_MAX_CONNECTIONS, process=get_docs_by_ids(data))
    step2  = Step(2, workers_count=EMBED_MAX_CONCURRENT_REQUESTS, queue_size=EMBED_MAX_CONCURRENT_REQUESTS * 2, process=embed)
    step3  = Step(3, workers_count=DB_MAX_CONNECTIONS // 2, queue_size=DB_MAX_CONNECTIONS, process=insert_embeddings)

    # Link steps
    step1.next(step2)
    step2.next(step3)
    
    # Run the pipeline until all data is processed
    # Register the callback function when a result is produced
    pipeline = Pipeline([step1, step2, step3],  kwargs, on_result=partial(update_res, pbar))
    await pipeline.start(data)
    await pipeline.run_until_completed()


async def run_pipeline(data: Iterable, **kwargs: dict):
    """
    Run the embedding pipeline.

    Args:
        data (Iterable): Iterable of data to process.
        **kwargs (dict): Additional keyword arguments for configuration.
            pool (psycopg_pool.ConnectionPool): The database connection pool.
            base_url (str): The base URL for processing.
            force_update (bool): Whether to force update the data.
    """

    pbar = tqdm.tqdm(data)

    # Create steps
    step1  = Step(1, workers_count=DB_MAX_CONNECTIONS // 2, queue_size=DB_MAX_CONNECTIONS, process=get_docs_by_range)
    step2  = Step(2, workers_count=EMBED_MAX_CONCURRENT_REQUESTS, queue_size=EMBED_MAX_CONCURRENT_REQUESTS * 2, process=embed)
    step3  = Step(3, workers_count=DB_MAX_CONNECTIONS // 2, queue_size=DB_MAX_CONNECTIONS, process=insert_embeddings)

    # Link steps
    step1.next(step2)
    step2.next(step3)
    
    # Run the pipeline until all data is processed
    pipeline = Pipeline([step1, step2, step3],  kwargs, on_result=partial(update_res, pbar))
    await pipeline.start(data)
    await pipeline.run_until_completed()

if __name__ == "__main__":
    asyncio.run(embed_pipeline())
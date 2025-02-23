
"""This module contains functions to query the OpenAlex database."""

from polus.aithena.embed_openalex.utils.postgres_tools import sync_query, async_query
import psycopg_pool
from openalex_types.works import Work
from polus.aithena.common.utils import async_time_logger
from polus.aithena.common.logger import get_logger

logger = get_logger(__name__)

def sync_get_works_count(pool) -> int:
    """Get the total amount of works in the database."""
    schema_name = "openalex"
    table_name = "works"
    count_works_query = f"""
        SELECT COUNT(*)
        FROM {schema_name}.{table_name}
    """
    res = sync_query(count_works_query, pool)
    total_work_count = res[0][0]
    return total_work_count


@async_time_logger
async def get_works_count(pool) -> int:
    """Get the total amount of works in the database."""
    schema_name = "openalex"
    table_name = "works"
    count_works_query = f"""
        SELECT COUNT(*)
        FROM {schema_name}.{table_name}
    """
    res = await async_query(count_works_query, pool)
    total_work_count = res[0][0]
    return total_work_count


@async_time_logger
async def get_works_batch(offset, batch_size, pool) -> list[Work]:
    """Get a batch of works from the database.

    Args:
        pool: Database connection pool.
        offset (int): The offset to start from.
        batch_size (int): The size of the batch to retrieve.
    
    This implementation relies on a separate index table to get the works in a specific order.
    This vastly improves performance compared to the naive implementation.
    """
    try:
        schema_name = "openalex"
        table_name = "works"
        works_query = f"""
            SELECT *
            FROM {schema_name}.{table_name}
            INNER JOIN (
            SELECT {schema_name}.index_works.id FROM {schema_name}.index_works WHERE row_number >= {offset}
            AND row_number < {offset + batch_size}
            )
            indexes ON openalex.works.id = indexes.id;
        """
        res = await async_query(works_query, pool)
        works = [Work.from_sql(work) for work in res]
        assert len(works) == batch_size, f"At offset {offset}, Expected {batch_size} works, got {len(works)}"
    except Exception as e:
        msg = f"""Error in get_works_batch: {e}, check if index_works table exists. 
        Falling back to slow implementation."""
        logger.error(msg)
        works = get_works_batch_slow(pool, offset, batch_size)
    return works


@async_time_logger
async def get_works_batch_slow(pool, offset, batch_size) -> list[Work]:
    """Get a batch of works from the database.
    
    This requires a full table scan and is much slower than the optimized implementation.
    """
    schema_name = "openalex"
    table_name = "works"
    works_query = f"""
        SELECT *
        FROM {schema_name}.{table_name}
        ORDER BY id
        OFFSET {offset}
        LIMIT {batch_size}
    """
    res = await async_query(works_query, pool)
    works = [Work.from_sql(work) for work in res]
    assert len(works) == batch_size, f"Expected {batch_size} works, got {len(works)}"
    return works

async def add_embeddings(
        works: list[Work],
        embeddings: list[list[float]],
        pool: psycopg_pool,
        schema_name: str = "openalex",
        table_name: str = "nomic_embed_text_768",
        on_conflict: str = "DO NOTHING",
):
        """Add embeddings to the database."""

        # Filter out empty embeddings
        # Also need to cast values to float since psycopg will interpret some values as int.
        # TODO CHECK psycopg for improved handling
        valid_embeddings = [(list(map(float, embedding)), work.id) for work, embedding 
                      in zip(works, embeddings) 
                      if work.abstract_inverted_index is not None
                    ] 
        if not valid_embeddings:
            logger.debug("No embedding to insert")
            return

        values_str = ', '.join(f"(%s, %s)" for _ in valid_embeddings)
        values = [item for sublist in valid_embeddings for item in sublist]

        return await async_query(f"""
            INSERT INTO {schema_name}.{table_name} (embedding, work_id)
            VALUES {values_str}
            ON CONFLICT (work_id) {on_conflict}
            RETURNING work_id;
        """, values=values, pool=pool)

@async_time_logger
async def get_works_by_ids(pool: psycopg_pool.AsyncConnectionPool, ids: list[int]) -> list[Work]:
    """
    Get works from the database by their IDs.

    Args:
        pool: Database connection pool.
        ids (list[int]): The list of work IDs to retrieve.

    Returns:
        list[Work]: A list of Work objects.
    """
    schema_name = "openalex"
    table_name = "works"
    ids_str = ', '.join(map(str, ids))
    works_query = f"""
        SELECT *
        FROM {schema_name}.{table_name}
        WHERE id IN ({ids_str});
    """
    res = await async_query(works_query, pool)
    works = [Work.from_sql(work) for work in res]
    return works


@async_time_logger
async def set_empty_abstracts_to_null(pool: psycopg_pool.AsyncConnectionPool = None) -> list[int]:
    """This is a cleanup function to set empty abstracts to NULL in the database.
    """
    query = """
        UPDATE openalex.works
        SET abstract_inverted_index = NULL
        WHERE abstract_inverted_index::jsonb = '{}'::jsonb;
    """
    res = await async_query(query, pool)
    work_ids = [Work.from_sql(work).id for work in res]
    return work_ids


@async_time_logger
async def get_unembedded_work_ids(pool, include_empty_dict = True):
    """Get unembedded work ids from the database.
    
    The original openalex database has empty dictionaries as abstract_inverted_index so we 
    are getting false positives.
    Set include_empty_dict to False to find those false positives.

    Args:
        pool: Database connection pool.
        include_empty_dict: Include records with empty dictionaries as abstract_inverted_index.
    """
    if include_empty_dict:
        query = """
        SELECT w.id
        FROM openalex.works w
        LEFT JOIN openalex.nomic_embed_text_768 n
        ON w.id = n.work_id
        WHERE n.work_id IS NULL
        AND w.abstract_inverted_index IS NOT NULL AND w.abstract_inverted_index::jsonb != '{}'::jsonb
        """
    else:
        query = """
        SELECT w.id
        FROM openalex.works w
        LEFT JOIN openalex.nomic_embed_text_768 n
        ON w.id = n.work_id
        WHERE n.work_id IS NULL
        AND w.abstract_inverted_index IS NOT NULL AND w.abstract_inverted_index::jsonb == '{}'::jsonb
        """
    return await async_query(query, pool)
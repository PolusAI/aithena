
"""This module contains functions to query the OpenAlex database."""

from polus.aithena.embed_openalex.utils.postgres_tools import async_query
import psycopg_pool
from openalex_types.works import Work
from polus.aithena.common.utils import async_time_logger
from polus.aithena.common.logger import get_logger

logger = get_logger(__name__)

@async_time_logger
async def get_running_queries(
    db_name: str,
    pool: psycopg_pool.AsyncConnectionPool = None
    ) -> list[int]:
    """Get the ids of the works that are currently running queries in the database."""

    query = f"""
        SELECT
            pid,
            usename,
            datname,
            state,
            query,
            query_start,
            state_change,
            wait_event_type,
            wait_event
        FROM
            pg_stat_activity
        WHERE
            state != 'idle'
            AND datname = '{db_name}'
        ORDER BY
            query_start;
    """
    res = await async_query(query, pool)
    return res


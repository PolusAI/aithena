"""Simple test script to run a query."""

import asyncio
from polus.aithena.common.logger import get_logger
from polus.aithena.embed_openalex.utils.admin_openalex_queries import get_running_queries
from polus.aithena.embed_openalex.utils.postgres_tools import get_async_pool_singleton
from polus.aithena.embed_openalex.config import (
    CONN_INFO, DB_MAX_CONNECTIONS, POSTGRES_DB
)

DB_CONN_TIMEOUT = 300

logger = get_logger(__name__)

async def run_query(
    conn_info=CONN_INFO,
    db_max_connections=DB_MAX_CONNECTIONS,
):
    """Run query.
    """

    pool = await get_async_pool_singleton(
        conn_info,
        db_max_connections,
        timeout=DB_CONN_TIMEOUT)
    
    res = await get_running_queries(POSTGRES_DB, pool)
    logger.info(f"Running queries: {res}")
    

if __name__ == "__main__":
    asyncio.run(run_query())
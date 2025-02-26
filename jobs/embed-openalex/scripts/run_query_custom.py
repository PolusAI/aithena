"""Simple test script to run a custom query."""

import asyncio
from polus.aithena.common.logger import get_logger
from polus.aithena.embed_openalex.utils.postgres_tools import async_query, get_async_pool_singleton
from polus.aithena.embed_openalex.config import (
    CONN_INFO, DB_CONN_TIMEOUT, DB_MAX_CONNECTIONS
)

logger = get_logger(__name__)

async def run_query(
    query: str,
    conn_info=CONN_INFO,
    db_max_connections=DB_MAX_CONNECTIONS,
):
    """Run query.
    """
    pool = await get_async_pool_singleton(
        conn_info,
        db_max_connections,
        timeout=DB_CONN_TIMEOUT)
    res = await async_query(query, pool)
    logger.info(res)

if __name__ == "__main__":
   query = f"SELECT id FROM openalex.works LIMIT 10;"

    # query = f"""
    # CREATE INDEX 
    # ON openalex.nomic_embed_text_768 
    # USING hnsw (embedding vector_cosine_ops) 
    # WITH (m = 48, ef_construction = 100);
    # """

    asyncio.run(run_query(query))
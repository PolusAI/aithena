import asyncio
import threading
from dotenv import load_dotenv
import psycopg_pool
from polus.aithena.common.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

thread_lock = threading.Lock()
asyncio_lock = asyncio.Lock()
POOL: psycopg_pool.AsyncConnectionPool = None

async def get_async_pool_singleton(
        conn_info: str = None,
        db_max_connections: int = None,
        db_min_connections : int = 4,
        timeout : int = 300,
        thread_safe: bool = False
    ) -> psycopg_pool.AsyncConnectionPool:
    """Get a connection pool for async operations.
    
    Args:
        conn_info (str): The connection info for the database.
        db_max_connections (int): The maximum number of connections to the database.
        db_min_connections (int): The minimum number of connections to the database.
        timeout (int): The timeout for the connection pool.
        thread_safe (bool): Whether to use a thread-safe lock or an asyncio lock.
    """
    global POOL
    if conn_info is None:
        raise ValueError("Connection info must be provided to create a new pool.")
    if thread_safe:
        with thread_lock:
            if POOL is None:
                POOL = await get_async_pool(conn_info, db_max_connections, db_min_connections, timeout)
            return POOL
    else:
        async with asyncio_lock:
            if POOL is None:
                POOL = await get_async_pool(conn_info, db_max_connections, db_min_connections, timeout)
            return POOL


async def get_async_pool(
        conn_info: str ,
        db_max_connections: None,
        db_min_connections : int = 4,
        timeout=300
    ) -> psycopg_pool.AsyncConnectionPool:
    """Get a connection pool for async operations.
    
    Args:
        conn_info (str): The connection info for the database.
        db_max_connections (int): The maximum number of connections to the database.
        db_min_connections (int): The minimum number of connections to the database.
    """
    pool = psycopg_pool.AsyncConnectionPool(
        conn_info,
        open=False,
        max_size=db_max_connections,
        min_size=db_min_connections,
        timeout=timeout
    )
    await pool.open(wait=True)
    return pool


def get_pool(
        conn_info: str ,
        db_max_connections: int = None,
        db_min_connections : int = 4
    ) -> psycopg_pool.ConnectionPool:
    """Get a connection pool for sync operations.
    
    Args:
        conn_info (str): The connection info for the database.
        db_max_connections (int): The maximum number of connections to the database.
        db_min_connections (int): The minimum number of connections to the database.
    """
    return psycopg_pool.ConnectionPool(
        conn_info,
        open=False,
        max_size=db_max_connections,
        min_size=db_min_connections,
    )


async def async_query(query: str, pool: psycopg_pool.ConnectionPool = None, values = None):
    """Execute a query asynchronously and return the results.
    
    Args:
        query (str): The query to execute.
        pool (psycopg_pool.ConnectionPool): The connection pool to use.
        if not provided, the global pool will be used.
    """
    if pool is None:
        if POOL is None:
            raise ValueError(
                """Connection pool must be provided.
                Define a global pool or pass it as an argument.
                """)
        pool = POOL

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            if values:
                await cur.execute(query, values)
            else:
                await cur.execute(query)
            results = await cur.fetchall()
            await conn.commit()
            return results


def sync_query(query: str, pool: psycopg_pool.ConnectionPool):
    """Execute a query asynchronously, commit and return the results."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            return results
        conn.commit()
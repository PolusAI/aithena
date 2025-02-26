import asyncio
import asyncio
from pathlib import Path
from polus.aithena.common.logger import get_logger
from polus.aithena.embed_openalex.utils.openalex_queries import get_unembedded_work_ids
from polus.aithena.embed_openalex.utils.postgres_tools import get_async_pool_singleton
from polus.aithena.embed_openalex.config import (
    CONN_INFO
)

DB_CONN_TIMEOUT = 300

logger = get_logger(__name__)

async def save_unembedded_work_ids(
    file_path,
    conn_info=CONN_INFO,
):
    """Save unembedded work ids to a file.
    
    Args:
        file_path: Path to the file where the unembedded work ids will be saved.
        conn_info: Database connection info.
        db_max_connections: Maximum number of database connections.
    """
    
    pool = await get_async_pool_singleton(conn_info)
    res = await get_unembedded_work_ids(pool)
    with open(file_path, 'w', newline='') as file:
        for record in res:
            file.write(f"{record}\n")

    logger.info(f"unembedded work ids saved to {file_path}")


def get_unembedded_work_ids_from_file(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                # Remove parentheses and split by comma
                id = line.strip('()').split(',')[0]
                # Convert to integers and yield as a tuple
                yield id


if __name__ == "__main__":
    file_path= Path('/polus2/gerardinad/projects/aithena/jobs/embed-openalex/logs/missing_records.txt')
    asyncio.run(save_unembedded_work_ids(file_path))
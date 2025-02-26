"""Attempt to parallelize the embedding process by using multiple workers to process different subsets of the data."""

import asyncio
import concurrent.futures
from polus.aithena.embed_openalex.utils.kubernetes_tools import get_pod_ips
from polus.aithena.embed_openalex.utils.postgres_tools import get_async_pool, get_pool, get_works_count, sync_get_works_count  
from polus.aithena.embed_openalex.batch_embed import embed_pipeline 
from polus.aithena.common.logger import get_logger
from polus.aithena.embed_openalex.config import (
    CUTOFF, OFFSET, WORKERS_COUNT, CONN_INFO, DB_MAX_CONNECTIONS, DB_FORCE_UPDATE,
    EMBED_MAX_CONCURRENT_REQUESTS, EMBED_BATCH_SIZE, OLLAMA_HOST, OLLAMA_PORT
)

logger = get_logger(__name__)

def worker_task(worker_id, total_works_count, offset, cutoff, ollama_url):
    """
    Worker task to process a subset of records.
    """
    logger.info(f"Worker {worker_id} processing {cutoff} records starting {offset}/{total_works_count}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(embed_pipeline(
        EMBED_MAX_CONCURRENT_REQUESTS, EMBED_BATCH_SIZE, 
        CONN_INFO, DB_MAX_CONNECTIONS,
        cutoff=cutoff, offset=offset, base_url=ollama_url, worker_id=worker_id,
        force_update=DB_FORCE_UPDATE
    ))
    loop.close()
    logger.info(f"Worker {worker_id} finished processing")
    return worker_id, result

async def main():
    # Get all ollama endpoints and instances count
    pod_ips = get_pod_ips(namespace="ollama")
    pod_urls = [f"http://{ip}:{OLLAMA_PORT}" for ip in pod_ips]
    logger.debug(f"ollama instances count: {len(pod_urls)}")
    logger.debug(f"ollama instances base urls: {pod_urls}")

    if OLLAMA_HOST:
        pod_urls = [f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"] * len(pod_urls)
        logger.info("OLLAMA_HOST is set, using the service url for all workers.")

    if WORKERS_COUNT > 0:
        workers_count = WORKERS_COUNT
    else:
        workers_count = len(pod_urls)

    # Get the total number of records
    if CUTOFF > 0:
        total_works_count = CUTOFF
        logger.info(f"Total number of records to process: {total_works_count}")
    else:
        pool = get_pool(CONN_INFO, 1, 1)
        pool.open()
        total_works_count = sync_get_works_count(pool)
        pool.close()
        logger.info(f"Total number of records to process: {total_works_count}")
    
    # Adjust for requested offset
    if OFFSET <= 0:
        start_offset = 0
    elif OFFSET > total_works_count:
        raise ValueError(f"OFFSET {OFFSET} is greater than the total number of records {total_works_count}")
    elif OFFSET > 0:
        start_offset = OFFSET
        total_works_count -= start_offset
    logger.info(f"Starting at {start_offset}")
    logger.info(f"Total number of records to process: {total_works_count}")

    # Calculate the number of records each worker should process
    records_per_worker = total_works_count // workers_count
    offsets = [start_offset + i * records_per_worker for i in range(workers_count)]
    cutoffs = [records_per_worker] * (workers_count - 1) + [total_works_count - offsets[-1]]

    for offset, cutoff, url in zip(offsets, cutoffs, pod_urls):
        logger.debug(f"will process partition {offset} of size {cutoff} at {url}")

    total_processed = 0
    total_inserted = 0
    total_embeddable = 0
    # Create a process pool and distribute the work
    # Each worker will process a subset of the records using a given ollama url 
    # (if OLLAMA_HOST is set, all workers will use the same url and load balance will be handled by the service)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers_count) as executor:
        futures = [
            executor.submit(worker_task, worker_id, total_works_count, offset, cutoff, ip)
            for worker_id, (offset, cutoff, ip) in enumerate(zip(offsets, cutoffs, pod_urls))
        ]

        # Wait for all workers to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                r = future.result()
                logger.info(f"worker {r[0]} completed {r[1]}")
                total_processed += r[1][0]
                total_embeddable += r[1][1]
                total_inserted += r[1][2]
            except Exception as e:
                logger.error(f"Worker raised an exception: {e}")
                executor.shutdown(wait=False, cancel_futures=True)
                raise
        
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Total embedable: {total_embeddable}")
    logger.info(f"Total inserted: {total_inserted}")


if __name__ == "__main__":
    """Main entry point."""
    asyncio.run(main())
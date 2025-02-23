"""Attempt to scale further by dimensioning the number of workers based on the number of CPUs available."""

import asyncio
import concurrent.futures
import os
from polus.aithena.common.utils import async_time_logger
from polus.aithena.embed_openalex.utils.kubernetes_tools import get_pod_ips
from polus.aithena.embed_openalex.utils.postgres_tools import get_async_pool, get_pool, get_works_count, sync_get_works_count  
from polus.aithena.embed_openalex.batch_embed import embed_pipeline 
from polus.aithena.common.logger import get_logger
from polus.aithena.embed_openalex.config import (
    CUTOFF, OFFSET, WORKERS_COUNT, CONN_INFO, DB_MAX_CONNECTIONS, DB_FORCE_UPDATE,
    EMBED_MAX_CONCURRENT_REQUESTS, EMBED_BATCH_SIZE, OLLAMA_HOST, OLLAMA_PORT
)

logger = get_logger(__name__)

async def process_partition(worker_id, offset, cutoff, ollama_url):
    logger.info(f"Worker {worker_id}: Processing partition {offset} of size {cutoff} with {ollama_url}")
    return await embed_pipeline(
        EMBED_MAX_CONCURRENT_REQUESTS, EMBED_BATCH_SIZE, 
        CONN_INFO, DB_MAX_CONNECTIONS,
        cutoff=cutoff, offset=offset, base_url=ollama_url, worker_id=0,
        force_update=DB_FORCE_UPDATE
    )

# Worker function to run in a separate process
def worker_task(worker_id, offset, cutoff, ollama_url):
    return asyncio.run(process_partition(worker_id, offset, cutoff, ollama_url))

@async_time_logger
async def main():

    num_cpus = os.cpu_count()
    logger.info(f"Number of CPUs: {num_cpus}")

#    # Get all ollama endpoints and instances count
#     pod_ips = get_pod_ips(namespace="ollama")
#     pod_urls = [f"http://{ip}:{OLLAMA_PORT}" for ip in pod_ips]
#     logger.debug(f"ollama instances count: {len(pod_urls)}")
#     logger.debug(f"ollama instances base urls: {pod_urls}")

    # if OLLAMA_HOST:
    #     pod_urls = [f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"] * len(pod_urls)
    #     logger.info("OLLAMA_HOST is set, using the service url for all workers.")

    if WORKERS_COUNT > 0:
        workers_count = WORKERS_COUNT
    else:
        # workers_count = len(pod_urls)
        workers_count = num_cpus // 2

    pod_urls = [f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"] * workers_count
        
    # Get the total number of records
    if CUTOFF > 0:
        total_works_count = CUTOFF
        logger.info(f"Total number of records to process: {total_works_count}")
    else:
        # TODO REMOVE  - to speed up testing
        total_works_count = 258602038
        # pool = await get_async_pool(CONN_INFO, 1, 1)
        # await pool.open()
        # total_works_count = await get_works_count(pool)
        # pool.close()
        # logger.info(f"Total number of records to process: {total_works_count}")
    
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
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers_count) as pool:
        tasks = [pool.submit(worker_task, worker_id, offset, cutoff, url) for worker_id, (offset, cutoff, url) in enumerate(zip(offsets, cutoffs, pod_urls))]
        for task in concurrent.futures.as_completed(tasks):
            try:
                worker_id, (processed, embeddable, inserted) = task.result()
                logger.info(f"worker {worker_id} completed: processed {processed}, embeddable {embeddable}, inserted {inserted}")
                total_processed += processed
                total_embeddable += embeddable
                total_inserted += inserted
            except Exception as e:
                logger.error(f"Worker raised an exception: {e}")
                pool.shutdown(wait=False, cancel_futures=True)
                raise
        
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Total embedable: {total_embeddable}")
    logger.info(f"Total inserted: {total_inserted}")
    
if __name__ == '__main__':
    asyncio.run(main())
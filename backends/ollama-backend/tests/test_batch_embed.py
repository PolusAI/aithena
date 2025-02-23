"""Benchmark batch embedding."""

import csv
from datetime import datetime
from pathlib import Path
import time
from dotenv import load_dotenv
import os
import httpx
from polus.aithena.common.utils import async_time_logger, time_logger
from polus.aithena.common.logger import get_logger
import asyncio
from tqdm.asyncio import tqdm
from llama_index.embeddings.ollama import OllamaEmbedding
from config import EXAMPLE_ABSTRACT
from compute_tokens import EXAMPLE_ABSTRACT_TOKENS_COUNT

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "50"))
INSTANCE_COUNT = int(os.getenv("INSTANCE_COUNT", "8"))

CONTEXT_WINDOW_SIZE = EXAMPLE_ABSTRACT_TOKENS_COUNT * BATCH_SIZE * MAX_CONCURRENT_REQUESTS
MAX_EMBEDDING_MODEL_BATCH_SIZE = CONTEXT_WINDOW_SIZE / EXAMPLE_ABSTRACT_TOKENS_COUNT

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:32437")
# OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
# OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:10434")
OLLAMA_URL = OLLAMA_HOST + "/api/embed"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
DEFAULT_HEADERS = { "Content-Type": "application/json"}
EMBEDDING_OPTIONS = {"num_ctx": CONTEXT_WINDOW_SIZE}
TOTAL_REQUESTS_COUNT = 4000

"""Configure llama index ollama client."""
ollama_embedding = OllamaEmbedding(
    model_name=EMBEDDING_MODEL,
    base_url=OLLAMA_HOST,
    ollama_additional_kwargs={"mirostat": 0},
)

def record_metrics_to_csv(max_concurrent_requests, batch_size, average_batch_processing_time, total_wall_time):
    """Record some benchmark metrics to CSV."""
    file_path = Path.cwd() / 'embedding_metrics_context.csv'
    file_exists = file_path.exists()

    with open(file_path, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'max_concurrent_requests', 'batch_size', 'average_batch_processing_time', 'total_wall_time', 'embedding_model', 'service_url',  'NUM_PARALLEL', 
 'OLLAMA_KEEP_ALIVE','OLLAMA_MAX_QUEUE']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'max_concurrent_requests': max_concurrent_requests,
            'batch_size': batch_size,
            'average_batch_processing_time': average_batch_processing_time,
            'total_wall_time': total_wall_time,
            'embedding_model': EMBEDDING_MODEL,
            'service_url': OLLAMA_HOST,
        })

@async_time_logger
async def embed_llama_index(texts: list[str]) -> list[float]:
    """Get embedding with Llama Index."""
    ollama_embedding = OllamaEmbedding(
        model_name=EMBEDDING_MODEL,
        base_url=OLLAMA_HOST,
        ollama_additional_kwargs={"mirostat": 0},
    )

    embeddings = await ollama_embedding.aget_text_embedding_batch(
        texts, show_progress=False
    )
    logger.debug(embeddings)
    return embeddings
    

@async_time_logger
async def embed(texts: list[str]) -> list[float]:
    """Get embedding through Aithena services.
    Args:
        texts: List of texts to embed.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_URL,
                headers=DEFAULT_HEADERS,
                json={
                    "model": EMBEDDING_MODEL,
                    "input": texts,
                    "truncate": False,
                    "keep_alive": -1,
                    "options": EMBEDDING_OPTIONS,
                }, timeout=120.0)
            response.raise_for_status()
            # logger.debug(f"Got response {response.json()}")
            return response.json()["embeddings"]
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url!r}.")
        raise ValueError(f"Failed to get embedding: {str(exc)}") from exc
    except httpx.HTTPStatusError as exc:
        logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        raise ValueError(f"Failed to get embedding: {exc.response.text}") from exc
    except httpx.ReadTimeout as exc:
        logger.error(f"Read timeout occurred while requesting {exc.request.url!r}.")
        raise ValueError(f"Failed to get embedding: Read timeout") from exc


def generate_abstracts(batch_size) -> list[str]:
    print(f"!!!!!!!!!! generate abstrcts size : {batch_size}")
    return [EXAMPLE_ABSTRACT] * batch_size

@async_time_logger
async def embed_pipeline(instance_count, max_concurrent_requests, batch_size, total_requests_count):
    progress_bar = tqdm(total=total_requests_count, desc="0/0")
    processed_count = 0
    total_batches = 0
    total_batch_time = 0

    start_time = time.time()

    for global_batch_index in range(0, total_requests_count, instance_count * max_concurrent_requests * batch_size):
        tasks = []
        # Process current set of batches.
        for batch_index in range(0, instance_count * max_concurrent_requests * batch_size, batch_size):
            if global_batch_index + batch_index + batch_size >= total_requests_count:
                remaining_requests = total_requests_count - (global_batch_index + batch_index)
                if remaining_requests <= 0:
                    break
                texts = generate_abstracts(remaining_requests)
            else:
                texts = generate_abstracts(batch_size)
            logger.debug(f"Added task offset {global_batch_index + batch_index}")
            tasks.append(embed(texts))

        batch_start_time = time.time()
        for task in asyncio.as_completed(tasks):
            embeddings = await task
            logger.debug(f"Processing {len(embeddings)} embeddings...")
            processed_count += len(embeddings)
            logger.info(f"Processed {processed_count}/{total_requests_count} embeddings.")
            progress_bar.update(batch_size)
            progress_bar.set_description(f"{processed_count}/{total_requests_count}")

        batch_end_time = time.time()
        total_batches += 1
        total_batch_time += (batch_end_time - batch_start_time)

    end_time = time.time()
    total_wall_time = end_time - start_time
    average_batch_processing_time = total_batch_time / total_batches if total_batches > 0 else 0

    progress_bar.close()

    # Record metrics to CSV
    record_metrics_to_csv(max_concurrent_requests, batch_size, average_batch_processing_time, total_wall_time)

if __name__ == "__main__":
    logger.debug(f"example abstract : {EXAMPLE_ABSTRACT}")
    logger.debug(f"example abstract token count : {EXAMPLE_ABSTRACT_TOKENS_COUNT}")
    logger.debug(f"max embedding model batch size : {MAX_EMBEDDING_MODEL_BATCH_SIZE}")
    run_pipeline = lambda: asyncio.run(embed_pipeline(INSTANCE_COUNT, MAX_CONCURRENT_REQUESTS, BATCH_SIZE, TOTAL_REQUESTS_COUNT))
    run_pipeline()
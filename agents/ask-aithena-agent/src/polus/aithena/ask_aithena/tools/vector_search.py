import httpx

from polus.aithena.ask_aithena.config import (
    LITELLM_URL,
    EMBEDDING_TABLE,
    ARCTIC_HOST,
    ARCTIC_PORT,
    HTTPX_TIMEOUT,
    AITHENA_LOG_LEVEL,
)
from polus.aithena.ask_aithena.logfire_logger import logfire
from faststream.rabbit import RabbitBroker
from polus.aithena.ask_aithena.rabbit import (
    ask_aithena_exchange,
    ask_aithena_queue,
    ProcessingStatus,
)
from polus.aithena.embeddings import ArcticClient, SNOWFLAKE_L_V2
import logging
from typing import Optional


logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)

ARCTIC_CLIENT = ArcticClient(host=ARCTIC_HOST, port=ARCTIC_PORT)

async def _embed_text(text: str) -> list[float]:
    """Embed text using OpenAI's embedding API.
    Not meant to be used directly. Use get_similar_works or get_similar_works_async instead.
    """
    logger.info(f"Embedding text: {text}")
    logfire.info(f"Embedding text: {text}")
    try:
        embedding = await ARCTIC_CLIENT.embed_query(text, model_name=SNOWFLAKE_L_V2)
        return embedding[0].tolist()
    except Exception as e:
        logger.error(f"Error embedding text: {e}")
        logfire.error(f"Error embedding text: {e}")
        raise e

async def get_similar_works_async(
    text: str,
    similarity_n: int,
    languages: list[str] | None,
    broker: Optional[RabbitBroker] = None,
    session_id: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> list[dict]:
    """Asynchronously get similar works from the database."""
    emb = await _embed_text(text)
    if broker is not None:
        await broker.publish(
            ProcessingStatus(
                status="finding_relevant_documents",
                message=f"Searching through my database...",
            ).model_dump_json(),
            exchange=ask_aithena_exchange,
            queue=ask_aithena_queue,
            routing_key=session_id,
        )
    try:
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            logfire.instrument_httpx(client)
            payload = {
                "vector": emb,
                "n": similarity_n,
                "table_name": EMBEDDING_TABLE,
                "languages": languages,
                "start_year": start_year,
                "end_year": end_year,
            }
            response = await client.post(
                f"{LITELLM_URL.rstrip('v1/')}/memory/pgvector/search_works",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting similar works asynchronously: {e}")
        logfire.error(f"Error getting similar works asynchronously: {e}")
        raise e

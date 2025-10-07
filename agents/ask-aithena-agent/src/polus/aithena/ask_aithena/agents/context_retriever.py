"""
This agent is used to retrieve the works that are most relevant to the query.
It uses the semantic agent to get the main topic of the query and then uses the vector search tool to get the works that are most relevant to the query.
"""

from polus.aithena.ask_aithena.agents.semantic_extractor import run_semantic_agent
from polus.aithena.ask_aithena.rabbit import (
    ask_aithena_exchange,
    ask_aithena_queue,
    ProcessingStatus,
)
from polus.aithena.ask_aithena.models import Context
from polus.aithena.ask_aithena.tools.vector_search import (
    get_similar_works_async,
)
from faststream.rabbit.broker import RabbitBroker
import logging
from typing import Optional
from polus.aithena.ask_aithena.logfire_logger import logfire
from polus.aithena.ask_aithena.config import USE_LOGFIRE
from polus.aithena.ask_aithena.config import AITHENA_LOG_LEVEL

if USE_LOGFIRE:
    logfire.instrument_openai()

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)


async def retrieve_context(
    query: str,
    similarity_n: int,
    languages: list[str] | None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    broker: Optional[RabbitBroker] = None,
    session_id: Optional[str] = None,
) -> Context:
    if USE_LOGFIRE:
        with logfire.span("context_retriever workflow"):
            logger.info(f"Running context retriever with query: {query}")
            logger.info("Running semantic extractor")
            semantics = await run_semantic_agent(query, broker, session_id)
            if broker is not None:
                await broker.publish(
                    ProcessingStatus(
                        status="searching_for_works",
                        message=f"Now I will search for works related to {semantics.output.sentence.lower()}...",
                    ).model_dump_json(),
                    exchange=ask_aithena_exchange,
                    queue=ask_aithena_queue,
                    routing_key=session_id,
                )
                logger.info("Running vector search")
            logger.info(f"Start year: {start_year}, End year: {end_year}, Languages: {languages}")
            works = await get_similar_works_async(
                semantics.output.sentence,
                similarity_n,
                languages,
                broker,
                session_id,
                start_year,
                end_year,
            )
            logger.info("Creating context")
            context = Context.from_works(works)
            return context
    else:
        logger.info(f"Running context retriever with query: {query}")
        logger.info("Running semantic extractor")
        semantics = await run_semantic_agent(query, broker, session_id)
        if broker is not None:
            await broker.publish(
                ProcessingStatus(
                    status="searching_for_works",
                    message=f"Now I will search for works related to {semantics.output.sentence.lower()}...",
                ).model_dump_json(),
                exchange=ask_aithena_exchange,
                queue=ask_aithena_queue,
                routing_key=session_id,
            )
        logger.info("Running vector search")
        logger.info(f"Start year: {start_year}, End year: {end_year}, Languages: {languages}")
        works = await get_similar_works_async(
            semantics.output.sentence,
            similarity_n,
            languages,
            broker,
            session_id,
            start_year,
            end_year,
        )
        logger.info("Creating context")
        context = Context.from_works(works)
        return context

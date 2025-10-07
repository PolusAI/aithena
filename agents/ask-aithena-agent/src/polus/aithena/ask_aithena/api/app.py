"""Main API application for the Ask Aithena agent."""

import json
import logging
import sys

from fastapi import FastAPI, Header, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from faststream.rabbit.fastapi import RabbitRouter
import httpx
from pydantic import BaseModel, Field
from typing import Optional
from polus.aithena.ask_aithena.config import (
    LOGFIRE_SERVICE_NAME,
    LOGFIRE_SERVICE_VERSION,
    LITELLM_URL,
    USE_LOGFIRE,
    RABBITMQ_URL,
    HTTPX_TIMEOUT,
)
from polus.aithena.ask_aithena.agents.context_retriever import retrieve_context
from polus.aithena.ask_aithena.agents.responder import responder_agent, PROMPT as RESPONDER_PROMPT
from polus.aithena.ask_aithena.agents.semantic_extractor import run_semantic_agent
from polus.aithena.ask_aithena.agents.talker import talker_agent
from polus.aithena.ask_aithena.models import Context
from polus.aithena.ask_aithena.agents.reranker.one_step_reranker import rerank_context
from polus.aithena.ask_aithena.agents.reranker.aegis import aegis_rerank_context
from polus.aithena.ask_aithena.rabbit import (
    ask_aithena_exchange,
    ask_aithena_queue,
    ProcessingStatus,
)
from polus.aithena.ask_aithena.config import SIMILARITY_N

from polus.aithena.ask_aithena.logfire_logger import logfire

if USE_LOGFIRE:
    logfire.configure(
        service_name=LOGFIRE_SERVICE_NAME,
        service_version=LOGFIRE_SERVICE_VERSION,
    )


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
    ],
)

# Configure specific loggers
logging.getLogger("uvicorn").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

rabbit_router = RabbitRouter(RABBITMQ_URL)


def broker():
    return rabbit_router.broker


async def _declare_exchanges_and_queues():
    """Declare the exchanges and queues for the Ask Aithena agent."""
    logger.info("Declaring exchanges and queues for the Ask Aithena agent.")
    try:
        await rabbit_router.broker.connect()
        exchange = await rabbit_router.broker.declare_exchange(ask_aithena_exchange)
        queue = await rabbit_router.broker.declare_queue(ask_aithena_queue)
        await queue.bind(exchange, routing_key="session.*")
    except Exception as e:
        logger.error(f"Error declaring exchanges and queues: {e}")
    finally:
        await rabbit_router.broker.close()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Create FastAPI app
    app = FastAPI(
        title="Ask Aithena API",
        description="RESTful API for Ask Aithena",
        version="1.0.0",
        on_startup=[_declare_exchanges_and_queues],
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    # Add health check endpoint
    @app.get("/", tags=["health"])
    async def health_check():
        """Ask Aithena API health check endpoint."""
        return {"status": "ok", "message": "Ask Aithena API is running"}

    @rabbit_router.get("/health", tags=["health"])
    async def detailed_health_check():
        """Detailed health check endpoint that verifies litellm connectivity."""
        health_info = {"status": "ok", "api": "running", "litellm": "unknown"}
        try:
            # Test litellm connection
            async with httpx.AsyncClient() as client:
                logfire.instrument_httpx(client, capture_headers=True)
                response = await client.get(f"{LITELLM_URL.strip('/v1')}/memory/health")
                if response.status_code == 200:
                    health_info["litellm"] = "connected"
                else:
                    health_info["litellm"] = "disconnected"
        except Exception as e:
            health_info["status"] = "degraded"
            health_info["litellm"] = "disconnected"
            health_info["litellm_error"] = str(e)
            logger.warning(f"Health check: litellm connection failed: {str(e)}")
        return health_info

    app.include_router(rabbit_router)
    logfire.instrument_fastapi(app)
    return app


# Create application instance for ASGI servers
app = create_application()


# Add the request model
class AskRequest(BaseModel):
    query: str
    similarity_n: int = Field(default=SIMILARITY_N)
    languages: list[str] | None = Field(default=["en"], description="The languages of the documents to retrieve. If not provided, all languages will be retrieved.")
    start_year: int | None = Field(default=None, description="The start year for filtering works.")
    end_year: int | None = Field(default=None, description="The end year for filtering works.")


class TalkerRequest(BaseModel):
    history: list[dict]


async def publish_status(broker, status: str, message: Optional[str], session_id: str):
    """Publish a status update to RabbitMQ for a specific session."""
    await broker.publish(
        ProcessingStatus(
            status=status,
            message=message,
        ).model_dump_json(),
        exchange=ask_aithena_exchange,
        queue=ask_aithena_queue,
        routing_key=session_id,
    )


@rabbit_router.post("/owl/ask")
@app.post("/owl/ask")
async def owl_ask(
    request: AskRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
):
    """Ask Aithena API endpoint for the Owl level."""
    logger.info(f"Received Owl ask request: {request.query} for session {x_session_id}")
    logfire.info(
        "Received Owl ask request", query=request.query, session_id=x_session_id
    )
    session_id = f"session.{x_session_id}"

    context_ = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
        rabbit_router.broker,
        session_id,
    )
    logger.info(f"Context: {context_.model_dump_json()}")
    logfire.info("Context retrieved", context=context_.model_dump())

    await publish_status(
        rabbit_router.broker,
        "preparing_response",
        f"I found {request.similarity_n} documents. Let me prepare my response...",
        session_id,
    )

    async def run_responder(query: str, context: Context):
        async with responder_agent.run_stream(
            f"""
            <question>{query}</question>
            {context.to_llm_context()}
            """
        ) as response:
            await publish_status(rabbit_router.broker, "responding", None, session_id)
            async for message in response.stream_text(delta=True):
                yield message
            yield "\n\n\n"
            yield context.to_references()

    return StreamingResponse(
        run_responder(request.query, context_), media_type="text/event-stream"
    )


@rabbit_router.post("/shield/ask")
@app.post("/shield/ask")
async def shield_ask(
    request: AskRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
):
    """Ask Aithena API endpoint for the Shield level."""
    logger.info(f"Received Shield ask request: {request.query}")
    logfire.info("Received Shield ask request", query=request.query)
    session_id = f"session.{x_session_id}"
    # Semantic Analysis and Context Retrieval
    context_norank = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
        rabbit_router.broker,
        session_id,
    )
    logger.info(f"Context: {context_norank.model_dump_json()}")
    logfire.info("Context retrieved", context=context_norank.model_dump())
    logger.info("Reranking context")
    await rabbit_router.broker.publish(
        ProcessingStatus(
            status="reranking_context",
            message="I got the documents, now I will double check them to make sure they are relevant to the question...",
        ).model_dump_json(),
        exchange=ask_aithena_exchange,
        queue=ask_aithena_queue,
        routing_key=session_id,
    )
    context_ = await rerank_context(request.query, context_norank)
    logger.info(f"Context: {context_.model_dump_json()}")
    logfire.info("Context reranked", context=context_.model_dump())
    await rabbit_router.broker.publish(
        ProcessingStatus(
            status="preparing_response",
            message="I am done checking the documents. Let me prepare my response...",
        ).model_dump_json(),
        exchange=ask_aithena_exchange,
        queue=ask_aithena_queue,
        routing_key=session_id,
    )

    async def run_responder(query: str, context: Context):
        async with responder_agent.run_stream(
            f"""
            <question>{query}</question>
            {context.to_llm_context()}
            """
        ) as response:
            await rabbit_router.broker.publish(
                "responding",
                exchange=ask_aithena_exchange,
                queue=ask_aithena_queue,
                routing_key=session_id,
            )
            async for message in response.stream_text(delta=True):
                yield message
            yield "\n\n\n"
            yield context.to_references()

    return StreamingResponse(
        run_responder(request.query, context_), media_type="text/event-stream"
    )


@rabbit_router.post("/aegis/ask")
@app.post("/aegis/ask")
async def aegis_ask(
    request: AskRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
):
    """Ask Aithena API endpoint for the Aegis level."""
    logger.info(f"Received Aegis ask request: {request.query}")
    logfire.info("Received Aegis ask request", query=request.query)
    session_id = f"session.{x_session_id}"
    # Semantic Analysis and Context Retrieval
    context_norank = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
        rabbit_router.broker,
        session_id,
    )
    logger.info(f"Context: {context_norank.model_dump_json()}")
    logfire.info("Context retrieved", context=context_norank.model_dump())
    logger.info("Reranking context very carefully")
    context_ = await aegis_rerank_context(
        request.query, context_norank, rabbit_router.broker, session_id
    )
    logger.info(f"Context: {context_.model_dump_json()}")
    logfire.info("Context reranked", context=context_.model_dump())
    await rabbit_router.broker.publish(
        ProcessingStatus(
            status="preparing_response",
            message="I am done checking the documents. Let me prepare my response...",
        ).model_dump_json(),
        exchange=ask_aithena_exchange,
        queue=ask_aithena_queue,
        routing_key=session_id,
    )

    async def run_responder(query: str, context: Context):
        async with responder_agent.run_stream(
            f"""
            <question>{query}</question>
            {context.to_llm_context()}
            """
        ) as response:
            await rabbit_router.broker.publish(
                "responding",
                exchange=ask_aithena_exchange,
                queue=ask_aithena_queue,
                routing_key=session_id,
            )
            async for message in response.stream_text(delta=True):
                yield message
            yield "\n\n\n"
            yield context.to_references()

    return StreamingResponse(
        run_responder(request.query, context_), media_type="text/event-stream"
    )

# @app.post("/talker/talk")
# async def talker_talk(
#     request: TalkerRequest,
#     x_session_id: str = Header(..., alias="X-Session-ID"),
# ):
#     """Ask Aithena API endpoint for the Talker level."""
#     session_id = f"session.{x_session_id}"
#     logger.info(f"Received Talker talk request for session {session_id}")
#     logfire.info("Received Talker talk request", history_length=len(request.history), session_id=session_id)

#     context_data = await redis_client.get_json(session_id)
#     if not context_data:
#         raise HTTPException(status_code=404, detail="Session context not found. Please start a new conversation.")

#     context = Context.model_validate(context_data)

#     async def run_talker(context: Context):
#         async with talker_agent.run_stream(
#             f"""
#             {context.to_llm_context()}
#             <history>{json.dumps(request.history)}</history>
#             """
#         ) as response:
#             async for message in response.stream_text(delta=True):
#                 yield message

#     return StreamingResponse(
#         run_talker(context), media_type="text/event-stream"
#     )

@app.post("/get-articles")
async def get_articles(
    request: AskRequest,
) -> list[dict]:
    """Get articles from the Ask Aithena API from similarity search."""
    logger.info(f"Received get articles request: {request.query}")
    logfire.info("Received get articles request", query=request.query)
    context_ = await retrieve_context(
        query=request.query,
        similarity_n=request.similarity_n,
        languages=request.languages,
        start_year=request.start_year,
        end_year=request.end_year,
    )
    return context_.to_list_for_mcp()

class GetArticleByDoiRequest(BaseModel):
    doi: str

@app.post("/get-article-by-doi")
async def get_article_by_doi(
    request: GetArticleByDoiRequest,
):
    """Get an article by its DOI."""
    logger.info(f"Received get article by DOI request: {request.doi}")
    logfire.info("Received get article by DOI request", doi=request.doi)
    try:
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            logfire.instrument_httpx(client)
            payload = {
                "doi": request.doi,
            }
            response = await client.post(
                f"{LITELLM_URL.rstrip('v1/')}/memory/pgvector/get_article_by_doi",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting article by DOI: {e}")
        logfire.error(f"Error getting article by DOI: {e}")
        raise e

class GetSemanticQueryRequest(BaseModel):
    query: str

@app.post("/get-semantic-query")
async def get_semantic_query(
    request: GetSemanticQueryRequest,
):
    """Get a semantic query from the Ask Aithena API."""
    logger.info(f"Received get semantic query request: {request.query}")
    logfire.info("Received get semantic query request", query=request.query)
    res = await run_semantic_agent(request.query)
    return res.output.sentence


@app.post("/answer-owl")
async def answer_owl(
    request: AskRequest,
):
    """Answer a question using the Owl level."""
    logger.info(f"Received answer owl request: {request.query}")
    logfire.info("Received answer owl request", query=request.query)
    context_ = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
    )
    response = await responder_agent.run(
        f"""
        <question>{request.query}</question>
        {context_.to_llm_context()}
        """
    )

    return f"Answer: {response.output}.\n\n References: {context_.to_references()}"

@app.post("/prompt-owl")
async def prompt_owl(
    request: AskRequest,
):
    """Generate a prompt to answer a question using the Owl level."""
    logger.info(f"Received prompt owl request: {request.query}")
    logfire.info("Received prompt owl request", query=request.query)
    context_ = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
    )
    prompt_ = [RESPONDER_PROMPT,
               f"\n\nHere is the question:\n<question>{request.query}</question>\nAnd here is the context:\n{context_.to_llm_context()}"]
    prompt_ = "\n".join(prompt_)

    return prompt_


@app.post("/answer-shield")
async def answer_shield(
    request: AskRequest,
):
    """Answer a question using the Shield level."""
    logger.info(f"Received answer shield request: {request.query}")
    logfire.info("Received answer shield request", query=request.query)
    context_norank = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
    )
    context_ = await rerank_context(request.query, context_norank)
    response = await responder_agent.run(
        f"""
        <question>{request.query}</question>
        {context_.to_llm_context()}
        """
    )

    return f"Answer: {response.output}.\n\n References: {context_.to_references()}"

@app.post("/prompt-shield")
async def prompt_shield(
    request: AskRequest,
):
    """Generate a prompt to answer a question using the Shield level."""
    logger.info(f"Received prompt shield request: {request.query}")
    logfire.info("Received prompt shield request", query=request.query)
    context_ = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
    )
    context_ = await rerank_context(request.query, context_)
    prompt_ = [RESPONDER_PROMPT,
               f"\n\nHere is the question:\n<question>{request.query}</question>\nAnd here is the context:\n{context_.to_llm_context()}"]
    prompt_ = "\n".join(prompt_)

    return prompt_

@app.post("/answer-aegis")
async def answer_aegis(
    request: AskRequest,
):
    """Answer a question using the Aegis level."""
    logger.info(f"Received answer aegis request: {request.query}")
    logfire.info("Received answer aegis request", query=request.query)
    context_norank = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
    )
    context_ = await aegis_rerank_context(request.query, context_norank)
    response = await responder_agent.run(
        f"""
        <question>{request.query}</question>
        {context_.to_llm_context()}
        """
    )

    return f"Answer: {response.output}.\n\n References: {context_.to_references()}"

@app.post("/prompt-aegis")
async def prompt_aegis(
    request: AskRequest,
):
    """Generate a prompt to answer a question using the Aegis level."""
    logger.info(f"Received prompt aegis request: {request.query}")
    logfire.info("Received prompt aegis request", query=request.query)
    context_ = await retrieve_context(
        request.query,
        request.similarity_n,
        request.languages,
        request.start_year,
        request.end_year,
    )
    context_ = await aegis_rerank_context(request.query, context_)
    prompt_ = [RESPONDER_PROMPT,
               f"\n\nHere is the question:\n<question>{request.query}</question>\nAnd here is the context:\n{context_.to_llm_context()}"]
    prompt_ = "\n".join(prompt_)

    return prompt_
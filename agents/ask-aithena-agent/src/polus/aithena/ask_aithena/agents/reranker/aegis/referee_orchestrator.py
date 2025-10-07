"""Reranker Agent Referee Orchestrator"""

from pathlib import Path
import logging

from polus.aithena.ask_aithena.config import (
    PROMPTS_DIR,
    LITELLM_URL,
    LITELLM_API_KEY,
    AITHENA_LOG_LEVEL,
)

from pydantic import Field, BaseModel, ConfigDict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from polus.aithena.ask_aithena.models import Context
from polus.aithena.ask_aithena.agents.reranker.aegis.single_agent import (
    referee_agent,
    RefereeDeps,
)
from faststream.rabbit.broker import RabbitBroker
from polus.aithena.ask_aithena.rabbit import (
    ask_aithena_exchange,
    ask_aithena_queue,
    ProcessingStatus,
)
from typing import Optional
from polus.aithena.ask_aithena.config import USE_LOGFIRE, AEGIS_ORCHESTRATOR_MODEL, AEGIS_ORCHESTRATOR_TEMPERATURE
from polus.aithena.ask_aithena.logfire_logger import logfire

if USE_LOGFIRE:
    logfire.instrument_openai()

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)

PROMPT = Path(PROMPTS_DIR, "reranker", "referee", "orchestrator.txt").read_text()


class AegisRerankedWork(BaseModel):
    """A reranked work."""

    index: int = Field(..., description="The index of the work")
    score: float = Field(..., description="The relevance score of the work")
    reason: str = Field(..., description="The reason for the score")


class AegisRerankerDeps(BaseModel):
    """Dependencies for the Reranker Agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    query: str = Field(..., description="The original user query")
    works: Context = Field(..., description="The list of works to rerank")
    broker: Optional[RabbitBroker] = Field(
        None, description="The RabbitMQ broker to use for the reranking"
    )
    session_id: Optional[str] = Field(
        None, description="The session ID to use for the status updates"
    )


model = OpenAIModel(
    AEGIS_ORCHESTRATOR_MODEL,
    provider=OpenAIProvider(base_url=LITELLM_URL, api_key=LITELLM_API_KEY),
)

aegis_reranker_agent = Agent(
    model=model,
    system_prompt=PROMPT,
    deps_type=AegisRerankerDeps,
    output_type=list[AegisRerankedWork],
    model_settings=ModelSettings(temperature=AEGIS_ORCHESTRATOR_TEMPERATURE),
)


@aegis_reranker_agent.system_prompt
async def system_prompt(ctx: RunContext[AegisRerankerDeps]) -> str:
    """System prompt for the Reranker Agent."""

    indx = [_ for _ in range(len(ctx.deps.works.documents))]
    return f"<query>{ctx.deps.query}</query>\n<indices>{indx}</indices>"


@aegis_reranker_agent.tool
async def score_work(
    ctx: RunContext[AegisRerankerDeps], index: int, effective_prompt: str
) -> AegisRerankedWork:
    """Score a work.
    Args:
        index: the index of the work to score
        effective_prompt: the effective prompt to pass to the referee agent
    Returns:
        the relevance score of the work
    """

    deps = RefereeDeps(
        query=ctx.deps.query, work=ctx.deps.works.works_for_reranker[index]
    )
    res = await referee_agent.run(effective_prompt, deps=deps)
    return AegisRerankedWork(index=index, score=res.output.score, reason=res.output.reason)


@aegis_reranker_agent.tool
async def publish_status(ctx: RunContext[AegisRerankerDeps], summary: str) -> None:
    """Publish a status update.

    Use this tool to publish a status update to the RabbitMQ queue.
    This must be done before starting the reranking process and before returning the final result.
    Also, YOU MUST use this tool to keep the user informed about the progress of the reranking process.
    Call this tool OFTEN!
    If calling this tool before starting the reranking process, you should pass a description of what you will do.
    If calling this tool after the reranking process, you should pass a summary of the process.
    If calling this tool in the middle of the reranking process, you should pass a summary of the process so far and hint
    at what you will do next.
    You need to call this tool OFTEN! CALL IT after 3-4 score_work calls. User NEEDS to know what's going on.
    Keep the summaries between 1 and 3 sentences. Use first person and a conversational tone. Finish with three dots (...)
    DO NOT talk about 'reranking', keep your sentences conversational and not too technical.

    Args:
        summary: the summary of the reranking process, MUST BE IN FIRST PERSON
    """
    if ctx.deps.broker is None:
        logger.info(f"No broker in Aegis, message: {summary}")
        logfire.info(f"No broker in Aegis, message: {summary}")
        return
    await ctx.deps.broker.publish(
        ProcessingStatus(
            status="reranking_context",
            message=summary,
        ).model_dump_json(),
        exchange=ask_aithena_exchange,
        queue=ask_aithena_queue,
        routing_key=ctx.deps.session_id,
    )


async def aegis_rerank_context(
    query: str,
    context: Context,
    broker: Optional[RabbitBroker] = None,
    session_id: Optional[str] = None,
) -> Context:
    """Rerank the context based on the query."""
    if USE_LOGFIRE:
        with logfire.span("aegis_rerank_context"):
            logger.info(f"Aegis Reranking context for query: {query}")
            logger.info(f"Context: {context.model_dump_json()}")
            reranked_data = await aegis_reranker_agent.run(
                "You are an expert reranker who's super careful",
                deps=AegisRerankerDeps(
                    query=query, works=context, broker=broker, session_id=session_id
                ),
            )
            logger.info(f"Reranked data: {reranked_data.output}")
            reranker_inds = [x.index for x in reranked_data.output]
            reranker_scores = [x.score for x in reranked_data.output]
            reranker_reasons = [x.reason for x in reranked_data.output]
            context.reranked_indices = reranker_inds
            context.reranked_scores = reranker_scores
            context.reranked_reasons = reranker_reasons
            return context
    else:
        logger.info(f"Aegis Reranking context for query: {query}")
        logger.info(f"Context: {context.model_dump_json()}")
        reranked_data = await aegis_reranker_agent.run(
            "You are an expert reranker who's super careful",
            deps=AegisRerankerDeps(
                query=query, works=context, broker=broker, session_id=session_id
            ),
        )
        logger.info(f"Reranked data: {reranked_data.output}")
        reranker_inds = [x.index for x in reranked_data.output]
        reranker_scores = [x.score for x in reranked_data.output]
        reranker_reasons = [x.reason for x in reranked_data.output]
        context.reranked_indices = reranker_inds
        context.reranked_scores = reranker_scores
        context.reranked_reasons = reranker_reasons
        return context
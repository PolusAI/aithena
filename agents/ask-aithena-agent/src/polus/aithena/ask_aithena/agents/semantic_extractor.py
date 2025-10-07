"""
This module contains the logic for the semantic agent.
It is a self-supervised agent that will extract a sentence from a user query.
"""

from pathlib import Path
from typing import Optional
import logging
from pydantic import Field, BaseModel
from polus.aithena.ask_aithena.config import (
    LITELLM_URL,
    LITELLM_API_KEY,
    SEMANTICS_MODEL,
    SEMANTICS_TEMPERATURE,
    PROMPTS_DIR,
)
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from faststream.rabbit import RabbitBroker
from polus.aithena.ask_aithena.rabbit import (
    ask_aithena_exchange,
    ask_aithena_queue,
    ProcessingStatus,
)
from polus.aithena.ask_aithena.config import USE_LOGFIRE, AITHENA_LOG_LEVEL
from polus.aithena.ask_aithena.logfire_logger import logfire

if USE_LOGFIRE:
    logfire.instrument_openai()

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)

PROMPTS_DIR = PROMPTS_DIR.joinpath("semantics")
EXTRACT_SEMANTICS_AGENT_PROMPT = Path(PROMPTS_DIR, "extract_agent.txt").read_text()
MAIN_AGENT_PROMPT = Path(PROMPTS_DIR, "main_agent.txt").read_text()


class ExtractSemanticAgentDeps(BaseModel):
    """User's original query, we want to extract the main topic from this query."""

    query: str = Field(..., description="The original user query")
    extra_instructions: Optional[str] = Field(
        None,
        description="Optional important considerations that you should take into account when extracting the main topic from the user's query.",
    )


class ExtractSemanticAgentOutput(BaseModel):
    """Sentence that captures the main idea of the question in an appropriate syntax for vector embedding."""

    sentence: str = Field(
        ...,
        description="The sentence that captures the main idea of the question in an appropriate syntax for vector embedding.",
    )


class SemanticAgentOutput(BaseModel):
    """Sentence that captures the main idea of the question in an appropriate syntax for vector embedding."""

    sentence: str = Field(
        ...,
        description="The sentence that captures the main idea of the question in an appropriate syntax for vector embedding.",
    )

semantic_extractor_model = OpenAIModel(
    model_name=SEMANTICS_MODEL,
    provider=OpenAIProvider(
        base_url=LITELLM_URL,
        api_key=LITELLM_API_KEY,
    ),
)

semantic_extractor_agent = Agent(
    model=semantic_extractor_model,
    system_prompt=EXTRACT_SEMANTICS_AGENT_PROMPT,
    output_type=ExtractSemanticAgentOutput,
    deps_type=ExtractSemanticAgentDeps,
    instrument=USE_LOGFIRE,
    model_settings=ModelSettings(
        temperature=SEMANTICS_TEMPERATURE,
    ),
)

@semantic_extractor_agent.system_prompt
async def semantic_extractor_system_prompt(ctx: RunContext[ExtractSemanticAgentDeps]) -> str:
    return f"User query: {ctx.deps.query}\nExtra instructions: {ctx.deps.extra_instructions}"

semantic_judge_model = OpenAIModel(
    model_name="gpt-4.1",
    provider=OpenAIProvider(
        base_url=LITELLM_URL,
        api_key=LITELLM_API_KEY,
    ),
)

semantic_agent = Agent(
    model=semantic_judge_model,
    system_prompt=MAIN_AGENT_PROMPT,
    output_type=SemanticAgentOutput,
    instrument=USE_LOGFIRE,
    model_settings=ModelSettings(
        temperature=SEMANTICS_TEMPERATURE,
    ),
)


@semantic_agent.tool_plain
async def extract_semantics(
    query: str, extra_instructions: Optional[str] = None
) -> str:
    """Extract the main idea of the question in an appropriate syntax for vector embedding.
    This calls an 'expert' LLM that will extract a potential sentence S from user query Q.

    Args:
        query: The original user query
        extra_instructions: optional important considerations passed to the expert LLM.
    """

    deps = ExtractSemanticAgentDeps(query=query, extra_instructions=extra_instructions)
    res = await semantic_extractor_agent.run(deps=deps)
    return res.output.sentence


async def run_semantic_agent(
    query: str, broker: Optional[RabbitBroker] = None, session_id: Optional[str] = None
) -> SemanticAgentOutput:
    """Run the semantic agent on a query.

    Args:
        query: The original user query
        broker: The broker to use to publish status messages
        session_id: The session ID to use for the status messages
    """
    if broker is not None:
        await broker.publish(
            ProcessingStatus(
                status="analyzing_query", message=f"Analyzing your question..."
            ).model_dump_json(),
            exchange=ask_aithena_exchange,
            queue=ask_aithena_queue,
            routing_key=session_id,
        )

    res = await semantic_agent.run(f"Q: {query}")

    return res

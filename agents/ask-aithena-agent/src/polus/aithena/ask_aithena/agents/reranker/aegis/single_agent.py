"""Referee Agent (ScoreGiver) for the Reranker."""

from polus.aithena.ask_aithena.config import (
    PROMPTS_DIR,
    LITELLM_URL,
    LITELLM_API_KEY,
)
import logging
from pydantic import Field, BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from polus.aithena.ask_aithena.agents.reranker.aegis.tools import (
    robust_noun_phrase_overlap as robust_tool,
    simplified_ngram_overlap as simplified_tool,
)
from polus.aithena.ask_aithena.config import USE_LOGFIRE, AEGIS_REFEREE_MODEL, AEGIS_REFEREE_TEMPERATURE, AITHENA_LOG_LEVEL
from polus.aithena.ask_aithena.logfire_logger import logfire

if USE_LOGFIRE:
    logfire.instrument_openai()

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)

PROMPTS_DIR = PROMPTS_DIR.joinpath("reranker", "referee")

with PROMPTS_DIR.joinpath("single_agent.txt").open("r") as f:
    logger.info(
        "Loading Referee Agent Prompt from %s", PROMPTS_DIR.joinpath("single_agent.txt")
    )
    REFREEE_AGENT_PROMPT = f.read()


class RefereeDeps(BaseModel):
    """Dependencies for the Referee Agent."""

    query: str = Field(..., description="The original user query")
    work: str = Field(..., description="The work to score")


class Score(BaseModel):
    """A scored work."""

    score: float = Field(..., description="The score of the work")
    reason: str = Field(..., description="The reason for the score")


model = OpenAIModel(
    AEGIS_REFEREE_MODEL,
    provider=OpenAIProvider(base_url=LITELLM_URL, api_key=LITELLM_API_KEY),
)
referee_agent = Agent(
    model=model,
    system_prompt=REFREEE_AGENT_PROMPT,
    deps_type=RefereeDeps,
    instrument=USE_LOGFIRE,
    output_type=Score,
    model_settings=ModelSettings(temperature=AEGIS_REFEREE_TEMPERATURE),
)
topic_agent = Agent(
    model=model,
    system_prompt=(
        "You are an expert in evaluating the relevance of a work to a user's query."
        "Determine if the work's content addresses the query's subject matter at all. "
        "Identify the core topics of both and assess if there's meaningful topical intersection. "
        "Consider the following aspects in your evaluation:"
        "1. Does the work cover the main subject or domain of the query?"
        "2. Are the key concepts or entities from the query present in the work?"
        "3. Does the work discuss themes, problems, or questions related to the query?"
        "4. Would a user interested in the query's topic find value in the work's content?"
        "5. Even if terminology differs, does the work address the underlying topic of interest?"
        "Analyze both explicit and implicit topical connections between the query and work."
        "Return a score of exactly 1 if the work is on-topic and addresses the query's subject matter."
        "Return a score of exactly 0 if the work is completely unrelated to the query's subject."
        "Do not return intermediate values - this is a binary assessment of topical relevance."
    ),
    instrument=USE_LOGFIRE,
    output_type=int,
    model_settings=ModelSettings(temperature=AEGIS_REFEREE_TEMPERATURE),
)
intent_matching_agent = Agent(
    model=model,
    system_prompt=(
        "You are an expert in evaluating the intent of a work to a user's query."
        "Determine if the work's content addresses the query's intent at all. "
        "Analyze whether the work provides the type of information the user is seeking - "
        "such as an explanation, a solution, a comparison, a recommendation, etc. "
        "Consider the following aspects in your evaluation:"
        "1. Does the work directly answer what the user is asking for?"
        "2. Does the work provide the specific type of information requested (how-to, definition, analysis, etc.)?"
        "3. Is the work's purpose aligned with the user's goal (learning, solving a problem, making a decision)?"
        "4. Does the work address any implicit needs behind the query?"
        "Return a score between 0 and 1, where:"
        "- 1.0: The work's intent perfectly matches the query's intent"
        "- 0.7-0.9: The work's intent mostly aligns with the query's intent"
        "- 0.4-0.6: The work partially addresses the query's intent"
        "- 0.1-0.3: The work barely addresses the query's intent"
        "- 0.0: The work's intent is completely unrelated to the query's intent"
    ),
    instrument=USE_LOGFIRE,
    output_type=float,
    model_settings=ModelSettings(temperature=AEGIS_REFEREE_TEMPERATURE),
)


@referee_agent.system_prompt
def system_prompt(ctx: RunContext[RefereeDeps]) -> str:
    return f"""
    <query>{ctx.deps.query}</query>
    <work>{ctx.deps.work}</work>
    """


@referee_agent.tool_plain
async def topical_intersection(query: str, work: str) -> int:
    """
    Check if the work is on topic compared to the user's query.
    This is a measure of the meaningful topical intersection between the query and the work.

    Returns:
        int: 1 if on-topic, 0 if completely unrelated
    """
    prompt = f"""
    <query>{query}</query>
    <work>{work}</work>
    """
    res = await topic_agent.run(prompt)
    return res.output


@referee_agent.tool_plain
async def intent_matching(query: str, work: str) -> float:
    """
    Check if the work's intent matches the query's intent.
    This is a measure of the intent matching between the query and the work.

    Returns:
        float: 1 if the work's intent matches the query's intent, 0 if completely unrelated
    """
    prompt = f"""
    <query>{query}</query>
    <work>{work}</work>
    """
    res = await intent_matching_agent.run(prompt)
    return res.output


@referee_agent.tool_plain
async def robust_noun_phrase_overlap(query: str, work: str) -> float:
    """
    Check the robust noun phrase overlap between the query and the work.
    Returns:
        float: Overlap ratio (0 to 1), granular scoring. 1 if the work is completely on topic, 0 if completely unrelated
    """
    return robust_tool(query, work)


@referee_agent.tool_plain
async def simplified_ngram_overlap(query: str, work: str) -> float:
    """
    Check the simplified ngram overlap between the query and the work.
    Returns:
        float: Overlap ratio (0 to 1), granular scoring. 1 if the work is completely on topic, 0 if completely unrelated
    """
    return simplified_tool(query, work)

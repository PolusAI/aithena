from pathlib import Path
import orjson
import logging
from polus.aithena.ask_aithena.config import (
    PROMPTS_DIR,
    LITELLM_URL,
    LITELLM_API_KEY,
)

from pydantic import Field, BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from polus.aithena.ask_aithena.models import Context
from polus.aithena.ask_aithena.config import USE_LOGFIRE, SHIELD_MODEL, SHIELD_TEMPERATURE, AITHENA_LOG_LEVEL
from polus.aithena.ask_aithena.logfire_logger import logfire

if USE_LOGFIRE:
    logfire.configure()
    logfire.instrument_openai()

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)

PROMPTS_DIR = PROMPTS_DIR.joinpath("reranker")
RERANKER_AGENT_PROMPT = Path(PROMPTS_DIR, "one_step_agent.txt").read_text()
# RERANKER_CREATE_PROMPT = orjson.loads(
#     Path(PROMPTS_DIR, "create_prompt.json").read_text()
# )
# RERANKER_DESCRIBE_WORKS_PROMPT = orjson.loads(
#     Path(PROMPTS_DIR, "describe_works.json").read_text()
# )
# RERANKER_DEFINE_TOPIC_PROMPT = orjson.loads(
#     Path(PROMPTS_DIR, "define_topic.json").read_text()
# )
RERANKER_CREATE_PROMPT = Path(PROMPTS_DIR, "create_prompt.txt").read_text()
RERANKER_DESCRIBE_WORKS_PROMPT = Path(PROMPTS_DIR, "describe_works.txt").read_text()
RERANKER_DEFINE_TOPIC_PROMPT = Path(PROMPTS_DIR, "define_topic.txt").read_text()


class RerankerDeps(BaseModel):
    """Query and context for the reranker."""

    query: str = Field(..., description="The original user query")
    context: Context = Field(
        ...,
        description="The context that will be used to eventually generate the chat response from RAG",
    )


class RerankedWork(BaseModel):
    """A reranked work with its index and score."""

    index: int = Field(..., description="The index of the work")
    score: float = Field(..., description="The score of the work")


model = OpenAIModel(
    SHIELD_MODEL,
    provider=OpenAIProvider(base_url=LITELLM_URL, api_key=LITELLM_API_KEY),
)
reranker_agent = Agent(
    model=model,
    system_prompt=RERANKER_AGENT_PROMPT,
    deps_type=RerankerDeps,
    instrument=USE_LOGFIRE,
    output_type=list[RerankedWork],
    model_settings=ModelSettings(temperature=SHIELD_TEMPERATURE),
)


@reranker_agent.system_prompt
async def prepare_prompt(ctx: RunContext[RerankerDeps]) -> str:
    return f"""
    <query>{ctx.deps.query}</query>
    <works>{ctx.deps.context.to_works_for_reranker()}</works>
    """


@reranker_agent.tool
async def verify_result_list(ctx: RunContext[RerankerDeps], result: list[dict]) -> bool:
    """Validates the reranked result list for length, uniqueness, score range, and order.

    This tool should ALWAYS be run after using the `call_reranker` tool to ensure the reranking output is valid.

    Args:
        ctx (RunContext[RerankerDeps]): The context containing the original query and works.
        result (list): The reranked list of works, each with an 'index' and 'score'.

    Returns:
        bool: True if the result list is valid, False otherwise.

    Validation Criteria:
        - The length of the result list must match the number of works in the original context.
        - All indices in the result must be unique.
        - All scores must be between 0 and 1 (inclusive).
        - The scores must be sorted in descending order (most relevant to least relevant).

    If the result fails any of these checks, you should call the `call_reranker` tool again,
    and update the prompt to instruct: "make sure your result contains X UNIQUE indices in [0,1] and
    that the order of the results is from most relevant to least relevant", where X is the number of works.
    """
    if len(result) != len(ctx.deps.context.documents):
        return False
    if len(result) != len(set([x["index"] for x in result])):
        return False
    scores = [x["score"] for x in result]
    if any(score < 0 or score > 1 for score in scores):
        return False
    if sorted(scores, reverse=True) != scores:
        return False
    return True


class DefineTopicDeps(BaseModel):
    """User's original query, we want to extract the main topic from this query."""

    query: str = Field(..., description="The original user query")


class DefineTopicOutput(BaseModel):
    """The main broad topic of the user's original query that we extracted."""

    broad_topic: str = Field(..., description="The main broad topic of the query")

define_topic_agent = Agent(
    model=model,
    system_prompt=RERANKER_DEFINE_TOPIC_PROMPT,
    deps_type=DefineTopicDeps,
    instrument=USE_LOGFIRE,
    output_type=DefineTopicOutput,
    model_settings=ModelSettings(temperature=SHIELD_TEMPERATURE),
)

@define_topic_agent.system_prompt
async def system_prompt(ctx: RunContext[DefineTopicDeps]) -> str:
    return f"""
    <query>{ctx.deps.query}</query>
    """



@reranker_agent.tool
async def define_broad_topic(ctx: RunContext[RerankerDeps]) -> str:
    """
    Define the main broad topic of the query.
    For example, if query is "What is the best treatment for depression?",
    the broad topic could be "clinical depression" or "mental health" or "medicine".
    """
    res = await define_topic_agent.run(
        "You are an expert in defining the main broad topic of a user's query",
        deps=DefineTopicDeps(query=ctx.deps.query),
    )
    return res.output.broad_topic


class DescribeWorksDeps(BaseModel):
    """The original list of works, we want to describe each work in a concise manner."""

    works: str = Field(..., description="The original list of works")
    query: str = Field(..., description="The original user query")


class DescribeWorksOutput(BaseModel):
    """The description of the works in a concise manner."""

    description: str = Field(
        ...,
        description="The description of the works in the appropriate format",
    )


describe_works_agent = Agent(
    model=model,
    system_prompt=RERANKER_DESCRIBE_WORKS_PROMPT,
    deps_type=DescribeWorksDeps,
    instrument=USE_LOGFIRE,
    output_type=DescribeWorksOutput,
    model_settings=ModelSettings(temperature=SHIELD_TEMPERATURE),
)



@reranker_agent.tool
async def describe_works(ctx: RunContext[RerankerDeps]) -> str:
    """
    Describe the works in a concise manner.
    """
    res = await describe_works_agent.run(
        "You are an expert in describing works in a concise manner",
        deps=DescribeWorksDeps(
            works=ctx.deps.context.to_works_for_reranker(), query=ctx.deps.query
        ),
    )
    return res.output.description


class CreateRerankerPromptDeps(BaseModel):
    "Input for the reranker prompt agent."

    works: str = Field(..., description="The original list of works as a single string")
    broad_topic: str = Field(
        ..., description="The main broad topic of the user's query"
    )
    description: str = Field(
        ..., description="The description of the works as a single string"
    )


class CreateRerankerPromptOutput(BaseModel):
    "The generated prompt for the reranker."

    prompt: str = Field(..., description="The generated prompt for the reranker")

create_reranker_prompt_agent = Agent(
    model=model,
    system_prompt=RERANKER_CREATE_PROMPT,
    deps_type=CreateRerankerPromptDeps,
    instrument=USE_LOGFIRE,
    output_type=CreateRerankerPromptOutput,
    model_settings=ModelSettings(temperature=SHIELD_TEMPERATURE),
)

@create_reranker_prompt_agent.system_prompt
async def system_prompt(ctx: RunContext[CreateRerankerPromptDeps]) -> str:
    return f"""
    <works>{ctx.deps.works}</works>
    <broad_topic>{ctx.deps.broad_topic}</broad_topic>
    <description>{ctx.deps.description}</description>
    """


@reranker_agent.tool
async def create_reranker_prompt(
    ctx: RunContext[RerankerDeps],
    broad_topic: str,
    works_description: str,
) -> str:
    """
    Create a prompt for the reranker.

    Args:
        broad_topic: The main broad topic of the query
        works_description: The concise description of the works
    """
    res = await create_reranker_prompt_agent.run(
        deps=CreateRerankerPromptDeps(
            works=ctx.deps.context.to_works_for_reranker(),
            broad_topic=broad_topic,
            description=works_description,
        )
    )
    return res.output.prompt


class CallRerankerDeps(BaseModel):
    "Input for the reranker agent."

    query: str = Field(..., description="The original user query")
    main_topic: str = Field(..., description="The main broad topic of the query")
    works: str = Field(..., description="The original list of works")
    works_description: str = Field(
        ..., description="The concise description of the works"
    )
    instructions: str = Field(..., description="The instructions for the reranker")


class CallRerankerOutput(BaseModel):
    "The reranked list of works' indices."

    reranked_works: list[RerankedWork] = Field(
        ..., description="The reranked list of works' indices and their scores"
    )

CALL_RERANKER_PROMPT = """
You are an expert in reranking works based on a user's query.
Read the instructions and carefully implement all steps necessary.
Make sure you follow the output format specified in instructions."
"""

call_reranker_agent = Agent(
    model=model,
    system_prompt=CALL_RERANKER_PROMPT,
    deps_type=CallRerankerDeps,
    instrument=USE_LOGFIRE,
    output_type=CallRerankerOutput,
    model_settings=ModelSettings(temperature=SHIELD_TEMPERATURE),
)



@reranker_agent.tool
async def call_reranker(
    ctx: RunContext[RerankerDeps],
    main_topic: str,
    works_description: str,
    prompt: str,
) -> list:
    """
    Call the reranker with the prompt generated by create_reranker_prompt tool
    You will need to pass the original list of works, the main broad topic
    of the query, and the description of the works to the reranker.

    Args:
        main_topic: The main broad topic of the query generated by define_broad_topic tool
        works_description: The concise description of the works generated by describe_works tool
        prompt: The prompt for the reranker, generated by create_reranker_prompt tool
    """
    res = await call_reranker_agent.run(
        deps=CallRerankerDeps(
            query=ctx.deps.query,
            main_topic=main_topic,
            works=ctx.deps.context.to_works_for_reranker(),
            works_description=works_description,
            instructions=prompt,
        )
    )
    return res.output.reranked_works


async def rerank_context(query: str, context: Context) -> Context:
    """Rerank the context based on the query."""
    if USE_LOGFIRE:
        with logfire.span("one_step_reranker"):
            logger.info(f"One Step Reranking context for query: {query}")
            logger.info(f"Context: {context.model_dump_json()}")
            reranked_data = await reranker_agent.run(
                deps=RerankerDeps(query=query, context=context),
            )
            logger.info(f"Reranked data: {reranked_data.output}")
            reranker_inds = [x.index for x in reranked_data.output]
            reranker_scores = [x.score for x in reranked_data.output]
            context.reranked_indices = reranker_inds
            context.reranked_scores = reranker_scores
            return context
    else:
        logger.info(f"One Step Reranking context for query: {query}")
        logger.info(f"Context: {context.model_dump_json()}")
        reranked_data = await reranker_agent.run(
            deps=RerankerDeps(query=query, context=context),
        )
        logger.info(f"Reranked data: {reranked_data.output}")
        reranker_inds = [x.index for x in reranked_data.output]
        reranker_scores = [x.score for x in reranked_data.output]
        context.reranked_indices = reranker_inds
        context.reranked_scores = reranker_scores
        return context

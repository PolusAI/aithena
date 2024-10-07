"""Ollama integration with llama index."""

from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
import pytest
import logging

logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger(__file__)

@pytest.fixture
def llm():
    """Create an llama3.1 8B model served with Ollama."""
    return Ollama(model="llama3.1:latest", request_timeout=120.0)

@pytest.fixture
def llm_extra():
    """Create an llama3.1 8B model served with Ollama with extra parameters.
    NOTE: when used through llama-index, it seems that we can only set parameters when initializing the model.
    Most values should be provided as additional_kwargs:
    https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
    """
    return Ollama(model="llama3.1:latest", request_timeout=120.0, temperature=1.0, additional_kwargs={"top_k": 1})


"""Test 4 modes of operations: sync or async, with streamed response or not."""

def test_chat(llm, user_message: dict[str, str]):
    """Sync implementation of ollama chat integration."""
    messages = [ChatMessage(**user_message)]
    resp = llm.chat(messages)
    logger.info(f"output: {resp.message.content}")


def test_chat_sync_stream(llm, user_message):
    """Sync stream implementation of ollama chat integration."""
    messages = [ChatMessage(**user_message)]
    chunks = llm.stream_chat(messages)
    for chunk in chunks:
         print(chunk.delta, end="", flush=True)
    logger.info(f"output: {chunk.message.content}")
     

@pytest.mark.asyncio(scope="session")
async def test_chat_async(llm, user_message: dict[str, str]):
    """Async implementation of ollama chat integration."""
    messages = [ChatMessage(**user_message)]
    resp = await llm.achat(messages)
    logger.info(f"output: {resp.message.content}")


@pytest.mark.asyncio(scope="session")
async def test_chat_async_stream(llm, user_message: dict[str, str]):
    """Async stream implementation of ollama chat integration."""
    messages = [ChatMessage(**user_message)]
    chunks = await llm.astream_chat(messages)
    async for chunk in chunks: # NOTE the async for iterating the async generator
         print(chunk.delta, end="", flush=True)
    logger.info(f"output: {chunk.message.content}")


"""Other tests."""

def test_chat_with_extra_params(llm_extra, user_message: dict[str, str]):
    """Use an llm with custom parameters."""
    messages = [ChatMessage(**user_message)]
    resp = llm_extra.chat(messages)
    logger.info(f"output: {resp.message.content}")  
    #TODO add assert


def test_chat_get_raw_llm_response(llm, user_message: dict[str, str]):
    """We can get the raw llm response for llm specific info.
    For example for ollama, we can collect performance metrics.
    """
    messages = [ChatMessage(**user_message)]
    resp = llm.chat(messages)
    assert isinstance(resp.raw["total_duration"], int)


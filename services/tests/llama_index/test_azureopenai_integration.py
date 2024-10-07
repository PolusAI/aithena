"""AzureOpenAI integration with llama index."""

import os
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.llms import ChatMessage, ChatResponse, MessageRole
from openai.types.completion_usage import CompletionUsage
from openai.types.chat.chat_completion import ChatCompletion
import pytest
import logging
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger(__file__)

"""Document params required to set up the client."""
api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
model_name = os.getenv("AZURE_OPENAI_MODEL")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

logger.info(f"connecting to : {azure_endpoint}")

@pytest.fixture
def llm():
    """Build a AzureOpenAI client."""
    return AzureOpenAI(
        model=model_name,
        deployment_name=deployment_name,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
    )

def test_chat(llm, user_message: dict[str, str]):
    """Test chat with a model deployed on azure openai.

    Detail what kind of model we get out of the response.
    """
    messages = [ChatMessage(**user_message)]
    resp = llm.chat(messages)
    assert isinstance(resp, ChatResponse)
    assert isinstance(resp.message, ChatMessage)
    assert resp.message.role == MessageRole.ASSISTANT
    assert isinstance(resp.raw, ChatCompletion), resp.raw.__class__
    assert isinstance(resp.raw.usage, CompletionUsage)
    assert resp.raw.usage.total_tokens > 0



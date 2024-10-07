import os
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.llms import ChatMessage, ChatResponse, MessageRole
import logging
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger(__file__)


api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
model_name = os.getenv("AZURE_OPENAI_MODEL")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

logger.info(f"connecting to : {azure_endpoint}")

def user_message():
    return {'role': 'user', 'content': 'Why is the sky blue?'}

def llm():
    return AzureOpenAI(
        model=model_name,
        deployment_name=deployment_name,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
    )

def test_chat(llm, user_message: dict[str, str]):
    """Sync implementation of ollama chat integration."""
    messages = [ChatMessage(**user_message)]
    resp = llm.chat(messages)
    print(resp)



test_chat(llm(), user_message())
from polus.aithena.ai_review_app import config
from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import time_logger
import requests

logger = get_logger(__file__)

def get_chat_models():
    url = config.AITHENA_SERVICE_URL + f"/chat/list"
    logger.debug(f"Aithena services request: {url}")
    try:
        response = requests.get(url)   
    except requests.RequestException as e:
        msg = (f"Aithena services request Error: {url}.", f"Got: {e}")
        raise requests.RequestException(msg)
    logger.debug(f"Chat request response: {response}")
    response.raise_for_status()  # Raise an error for bad status codes
    result = response.json()
    logger.debug(f"Chat request result: {result}")
    return result


@time_logger
def chat_request(llm: str, messages: list[dict]):
    
    """Chat with the model."""
    url = config.AITHENA_SERVICE_URL + f"/chat/{llm}/generate"
    logger.debug(f"request answer from {url}")
    try:
        response = requests.post(
            url, json=messages, params={"stream": False}, stream=False
        )
    except requests.RequestException as e:
        msg = (f"Request Chat Error: {url}.", f"Got response: {e}")
        raise requests.RequestException(msg)
    logger.debug(f"Chat request response: {response}")
    response.raise_for_status()  # Raise an error for bad status codes
    result = response.json()
    logger.debug(f"Chat request result: {result}")

    return result

@time_logger
def chat_request_stream(llm: str, messages: list[dict]):
    
    """Chat with the model."""
    url = config.AITHENA_SERVICE_URL + f"/chat/{llm}/generate"
    logger.debug(f"request answer from {url}")
    try:
        response = requests.post(
            url, json=messages, params={"stream": True}, stream=True
        )
    except requests.RequestException as e:
        msg = (f"Request Chat Error: {url}.", f"Got response: {e}")
        raise requests.RequestException(msg)
    logger.debug(f"Chat request response: {response}")
    response.raise_for_status()  # Raise an error for bad status codes
    return response
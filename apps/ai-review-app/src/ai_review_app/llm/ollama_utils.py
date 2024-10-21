"""Utility functions for interacting with Ollama."""

# pylint: disable=too-many-arguments, W1203
import json
from typing import Callable, Optional

import solara
from aithena_services.llms.types.message import BaseMessage, UserMessage, AssistantMessage

from aithena_services.llms.ollama import Ollama
from solara.lab import task

from ..utils.common import get_logger

logger = get_logger(__file__)


@task
async def send_to_ollama(
    prompt: str,
    model: str,
    llm_context: str,
    query: str,
    set_llm_response: Optional[Callable] = None,
    message_history: Optional[solara.Reactive[list[BaseMessage]]] = None,
    stop_streaming: Optional[solara.Reactive[bool]] = solara.reactive(False),
):
    """Send a request to Ollama and stream the response.

    Args:
        prompt: The prompt to send to Ollama.
        model: The model to use for the request, must be available in Ollama instance.
        llm_context: The context to send to Ollama, enclosed in <context>...</context> tags.
        query: The query to send to Ollama, enclosed in <query>...</query> tags.
        set_llm_response: A function to set the `llm_response` reactive.
        set_task_pending: A function to set the `task_pending` state.
        stop_streaming: A reactive variable to stop the streaming loop.
    """
    message_content = f"""
<context>
{llm_context}
</context>
<query>
{query}
</query>
        """
    logger.info(f"message to send: {message_content}")
    message_to_send = UserMessage(role="user", content=message_content)
    message_history.value.append(message_to_send)
    ol = Ollama(
        name=model,
        prompt=prompt.replace("\n", ""),
        messages=message_history.value,
        stream=True,
        timeout=450,
    )
    response = ol.send()
    logger.info(f"message sent to Ollama, streaming response {response}")
    response_ = ""
    for chunk in response:
        if stop_streaming.value:
            logger.info("Stopping Ollama streaming loop...")
            stop_streaming.set(False)
            break
        if chunk:
            response_ += json.loads(chunk)["message"]["content"]
            set_llm_response(response_)

    message_history.value.append(AssistantMessage(content=response_))
    set_task_pending(False)
    logger.info("Finished streaming Ollama response")
    return


OLLAMA_AVAILABLE_MODELS: list[str] = Ollama.list_models()

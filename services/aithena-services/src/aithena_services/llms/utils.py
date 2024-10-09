"""LLM Utils."""

from typing import Sequence

from llama_index.core.base.llms.types import ChatMessage

from aithena_services.llms.types import Message


def cast_messages(messages: Sequence, is_dict: bool) -> Sequence[ChatMessage]:
    """Validate dict messages to Aithena Message and cast to li ChatMessage."""
    if is_dict:
        return [Message(**x).to_llamaindex() for x in messages]
    if all(isinstance(x, ChatMessage) for x in messages):  # for completions
        return messages
    return [x.to_llamaindex() for x in messages]  # x is Message


def check_messages(messages: Sequence) -> bool:
    """Check messages."""
    # completion calls will have ChatMessage
    return all(isinstance(x, (Message, dict, ChatMessage)) for x in messages)


def check_and_cast_messages(messages: Sequence) -> Sequence[ChatMessage]:
    """Check and cast messages."""
    if not check_messages(messages):
        if isinstance(messages, list):
            raise ValueError(
                f"Messages must be a sequence of type Message or dict. Got list of: {type(messages[0])}"
            )
        raise ValueError(
            f"Messages must be a sequence of type Message or dict. Got {type(messages)}"
        )
    if all(isinstance(x, dict) for x in messages):
        return cast_messages(messages, True)
    return cast_messages(messages, False)

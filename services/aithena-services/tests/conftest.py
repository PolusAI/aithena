"""Pytest configuration."""

import pytest

from aithena_services.llms.types import Message  # type: ignore


@pytest.fixture
def user_message():
    """Return user message as `dict`."""
    message = {"role": "user", "content": "Why is the sky blue?"}
    return message


@pytest.fixture
def math_question():
    """Return simple math question as `dict`."""
    return [{"role": "user", "content": "Is two greater than minus 2?"}]


@pytest.fixture
def text_question_1():
    """Return text question as `dict` asking for short story."""
    return [
        {
            "role": "user",
            "content": "You are a pirate who loves bears."
            + "Tell me a story in two sentences about a bear who loves peanut butter",
        }
    ]


@pytest.fixture
def query_1():
    """Return query as `Message` for testing."""
    return [
        Message(
            role="system",
            content="You are an expert in mathematic, physics"
            + " and meteorology. Your answers are only useful for other experts."
            + " You use always very technical and formal language to answer."
            + " You like jokes but usually you don't understand them."
            + " You answer in two or three sentences each time.",
        ),
        Message(role="user", content="Why does the moon follow me?"),
    ]

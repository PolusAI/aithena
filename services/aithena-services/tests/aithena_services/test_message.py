import json

import pytest
from pydantic import ValidationError

from aithena_services.llms.types.message import (
    AssistantMessage,
    ContentPartImage,
    ContentPartText,
    ImageUrl,
    Message,
    Role,
    SystemMessage,
    ToolMessage,
    UserMessage,
)


def test_user_message_creation():
    """Create UserMessage."""
    content = "Hello, world!"
    message = UserMessage(content=content)
    assert message.role == Role.USER
    assert message.content == content
    assert message.name is None


def test_user_message_creation_with_name():
    """Create UserMessage with name."""
    content = "Hello, world!"
    name = "aithenauser"
    message = UserMessage(content=content, name=name)
    assert message.role == Role.USER
    assert message.content == content
    assert message.name == name


def test_system_message_creation():
    """Create SystemMessage."""
    content = "System update"
    message = SystemMessage(content=content)
    assert message.role == Role.SYSTEM
    assert message.content == content
    assert message.name is None


def test_system_message_creation_with_name():
    """Create SystemMessage with name."""
    content = "System update"
    name = "aithenasystem"
    message = SystemMessage(content=content, name=name)
    assert message.role == Role.SYSTEM
    assert message.content == content
    assert message.name == name


def test_assistant_message_creation():
    """Create AssistantMessage."""
    message = AssistantMessage()
    assert message.role == Role.ASSISTANT
    assert message.name is None


def test_assistant_message_creation_with_name():
    """Create AssistantMessage with name."""
    name = "aithenaassistant"
    message = AssistantMessage(name=name)
    assert message.role == Role.ASSISTANT
    assert message.name == name


def test_tool_message_creation():
    """Create ToolMessage."""
    message = ToolMessage()
    assert message.role == Role.TOOL
    assert message.content is None


def test_tool_message_creation_with_content():
    """Create ToolMessage with content."""
    content = "Tool update"
    message = ToolMessage(content=content)
    assert message.role == Role.TOOL
    assert message.content == content


def test_message_as_dict():
    """Convert Message to dict."""
    user_message = Message(role="user", content="Hello, world!")
    message_dict = user_message.as_dict()
    assert isinstance(user_message.root, UserMessage)
    assert message_dict["role"] == "user"
    assert message_dict["content"] == "Hello, world!"


def test_message_as_json():
    """Convert Message to JSON."""
    user_message = Message(role="user", content="Hello, world!")
    message_dict = user_message.as_json()
    assert isinstance(user_message.root, UserMessage)
    assert message_dict["role"] == "user"
    assert message_dict["content"] == "Hello, world!"


def test_content_part_text():
    """Create ContentPartText."""
    content_part = ContentPartText(type="text", text="Sample text")
    assert content_part.type == "text"
    assert content_part.text == "Sample text"


def test_content_part_image():
    """Create ContentPartImage."""
    image_url = ImageUrl(url="http://example.com/image.png", detail="high")
    content_part = ContentPartImage(type="image_url", image_url=image_url)
    assert content_part.type == "image_url"
    assert content_part.image_url == image_url


def test_invalid_role():
    """Test invalid role."""
    with pytest.raises(ValidationError):
        UserMessage(role="invalid_role", content="Hello, world!")


def test_message_to_llamaindex():
    """Convert Message to LlamaIndex message."""
    message = Message(role="assistant", content="Hello, world!")
    llama_message = message.to_llamaindex()
    assert llama_message.role == "assistant"
    assert llama_message.content == "Hello, world!"


def test_message_additional_kwargs():
    """Test additional kwargs for Message."""
    user_message = Message(role="user", content="Hello, world!", name="test_user")
    additional_kwargs = user_message.additional_kwargs
    assert additional_kwargs == {"name": "test_user"}


def test_message_repr():
    """Test Message repr."""
    user_message = Message(role="user", content="Hello, world!", name="test_user")
    assert repr(user_message) == "Message(role=user, content=Hello, world!)"


def test_message_str():
    """Test Message str."""
    user_message = Message(role="user", content="Hello, world!", name="test_user")
    assert str(user_message) == "user: Hello, world!"


def test_getattr():
    """Test getting attributes from Message."""
    user_message = Message(role="user", content="Hello, world!", name="test_user")
    assert user_message.role == "user"
    assert user_message.content == "Hello, world!"
    assert user_message.name == "test_user"
    assert user_message.name == user_message.root.name
    assert user_message.content == user_message.root.content
    assert user_message.role == user_message.root.role


def test_role_frozen_1():
    """Test that role is frozen 1."""
    with pytest.raises(ValueError):
        UserMessage(role="system", content="Hello, world!")


def test_role_frozen_2():
    """Test that role is frozen 2."""
    user_message = Message(role="user", content="Hello, world!", name="test_user")
    with pytest.raises(ValidationError):
        user_message.role = Role.SYSTEM


def test_system_content_not_optional():
    """Test that content is not optional for SystemMessage."""
    with pytest.raises(ValidationError):
        Message(role="system", name="test_system")

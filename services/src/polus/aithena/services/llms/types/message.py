"""Message types for Aithena services."""

import enum
from typing import TYPE_CHECKING, Optional, Union, overload

from llama_index.core.base.llms.types import ChatMessage as LlamaIndexMessage
from pydantic import BaseModel, Field, RootModel
from typing_extensions import Annotated, Literal


class Role(str, enum.Enum):
    """Role of the message."""

    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    TOOL = "tool"


class BaseMessage(BaseModel):
    """Base class for all messages."""

    role: Role
    content: Optional[str] = None


# OpenAI
class BaseContentPart(BaseModel):
    """Base class for content parts."""

    type: Literal["text", "image_url"]


class ContentPartText(BaseContentPart):
    """Content part with text."""

    type: Literal["text"]
    text: str


class ImageUrl(BaseModel):
    """Image URL with optional detail level."""

    url: str
    detail: Literal["auto", "low", "high"] = "auto"


class ContentPartImage(BaseContentPart):
    """Content part with image URL."""

    type: Literal["image_url"]
    image_url: ImageUrl


ContentPart = Annotated[
    Union[ContentPartText, ContentPartImage], Field(discriminator="type")
]


class UserMessage(BaseMessage):
    """User message."""

    role: Literal[Role.USER] = Field(default=Role.USER, frozen=True)
    name: Optional[str] = Field(None, repr=False)
    content: Union[str, list[ContentPart]]  # type: ignore


class SystemMessage(BaseMessage):
    """System message."""

    role: Literal[Role.SYSTEM] = Field(default=Role.SYSTEM, frozen=True)
    content: str  # not optional
    name: Optional[str] = Field(None, repr=False)


class AssistantMessage(BaseMessage):
    """Assistant message."""

    role: Literal[Role.ASSISTANT] = Field(default=Role.ASSISTANT, frozen=True)
    name: Optional[str] = Field(None, repr=False)


class ToolMessage(BaseMessage):
    """Tool message."""

    role: Literal[Role.TOOL] = Field(default=Role.TOOL, frozen=True)


MessageRoot = Annotated[
    Union[UserMessage, SystemMessage, AssistantMessage], Field(discriminator="role")
]


class Message(RootModel):
    """Message for LLM."""

    root: MessageRoot

    if TYPE_CHECKING:

        @overload
        def __init__(self, role: str): ...
        @overload
        def __init__(self, role: str, content: Union[str, list[ContentPart]]): ...
        @overload
        def __init__(
            self, role: str, content: Union[str, list[ContentPart]], name: str
        ): ...

        def __init__(
            self,
            role: str,
            content: Optional[Union[str, list[ContentPart]]] = None,
            name: Optional[str] = None,
        ):  # for mypy compatibility
            root_ = {"role": role, "content": content, "name": name}
            super().__init__(**root_)

    def __getattr__(self, name):
        try:
            return getattr(self.root, name)
        except AttributeError:
            raise AttributeError(  # pylint: disable=W0707
                f"Message has no attribute {name}"
            )

    def __setattr__(self, name, value):
        if name == "root":
            super().__setattr__(name, value)
        else:
            setattr(self.root, name, value)

    def as_dict(self, **kwargs):
        """Wrapper for `self.model_dump(mode="python")`
        with `exclude_unset=True` and `exclude_none=True`.

        Additional keyword arguments are passed to `self.model_dump`.
        If these additional arguments include `exclude_unset` or `exclude_none`,
        these values will be ignored.
        """
        for key in ["exclude_unset", "exclude_none"]:
            if key in kwargs:
                kwargs.pop(key)
        return self.model_dump(
            mode="python", exclude_unset=True, exclude_none=True, **kwargs
        )

    def as_json(self, **kwargs):
        """Wrapper for `self.model_dump(mode="json")`
        with `exclude_unset=True` and `exclude_none=True`.

        Additional keyword arguments are passed to `self.model_dump`.
        If these additional arguments include `exclude_unset` or `exclude_none`,
        these values will be ignored.
        """
        for key in ["exclude_unset", "exclude_none"]:
            if key in kwargs:
                kwargs.pop(key)
        return self.model_dump(
            mode="json", exclude_unset=True, exclude_none=True, **kwargs
        )

    @property
    def additional_kwargs(self) -> dict:
        """Keyword arguments that are not `role` or `content`, for compatibility with LlamaIndex."""
        return self.root.model_dump(
            mode="python",
            exclude_unset=False,
            exclude_none=False,
            exclude={"role", "content"},
        )

    def to_llamaindex(self) -> LlamaIndexMessage:
        """Convert to LlamaIndex ChatMessage."""
        return LlamaIndexMessage(
            role=self.root.role.value,
            content=self.root.content,
            **self.additional_kwargs,
        )

    @classmethod
    def from_llamaindex(cls, llama_index_message: LlamaIndexMessage) -> "Message":
        """Create Aithena Message from LlamaIndex ChatMessage."""
        return cls(**llama_index_message.dict())

    def __repr__(self):
        return f"Message(role={self.root.role.value}, content={self.root.content})"

    def __str__(self) -> str:  # same as LlamaIndexMessage.__str__
        return f"{self.root.role.value}: {self.root.content}"

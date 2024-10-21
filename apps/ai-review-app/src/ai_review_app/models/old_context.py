"""Base Model for Context."""

from typing import Literal, Optional, Union
from typing_extensions import Self
from polus.aithena.common.logger import get_logger
from pydantic import BaseModel, model_validator

from .old_document import OldDocument

logger = get_logger(__name__)


class ContextPart(BaseModel):
    """Base Model for Context."""

    type: Literal["article", "user_input"]
    content: Union[OldDocument, str]
    id: Optional[str] = None  # TODO use UUID for user_input?

    @model_validator(mode="before")
    def validate_content_before(self) -> Self:
        if isinstance(self["content"], OldDocument):
            self["type"] = "article"
            self["id"] = self["content"].document_id
        elif isinstance(self["content"], str):
            self["type"] = "user_input"
            self["id"] = None
        elif isinstance(self["content"], dict):
            return self
        else:
            raise ValueError("content must be a Document or a str")
        return self

    def __hash__(self):
        return hash(self.type) + hash(self.content) + hash(self.id)

    @model_validator(mode="after")
    def validate_content_after(self) -> Self:
        """Make sure that the content is of the correct type.

        If the type is "article", the content must be a `Document`.
        If the type is "user_input", the content must be a `str`.
        """
        if self.type == "article":
            if not isinstance(self.content, OldDocument):
                raise ValueError("content must be a Document")
        if self.type == "user_input":
            if not isinstance(self.content, str):
                raise ValueError("content must be a str")
        return self

    @property
    def markdown_pretty(self) -> str:  # pylint: disable=R1710
        """Content as a pretty markdown string."""
        if self.type == "article":
            return f"article: {self.content.title}"
        if self.type == "user_input":
            return self.content

    @property
    def llm_text(self):  # pylint: disable=R1710
        """Content as a string for LLM."""
        if self.type == "article":
            return f"""
<article>
<title>{self.content.title}</title>
<authors>{self.content.authors_str}</authors>
<abstract>{self.content.abstract}</abstract></article>
""".replace(
                "\n", ""
            )
        if self.type == "user_input":
            return self.content

    def __repr__(self):
        if self.type == "article":
            return f"ContextPart(type={self.type}, title={self.content.title})"
        if self.type == "user_input":
            return f"ContextPart(type={self.type}, content={self.content})"
import datetime
from enum import Enum
from typing import ClassVar, Optional
import uuid
import numpy
from pydantic import BaseModel, ConfigDict, Field

from ai_review_app.models.prompts import PROMPT_CONVERSE
from aithena_services.llms.types import Message

class DocType(str, Enum):
    DOCUMENT= "DOCUMENT"
    ABSTRACT = "ABSTRACT",
    CHUNK = "CHUNK",
    SUMMARY = "SUMMARY"
    USER_TEXT = "USER_TEXT"

DOCUMENT_TAG = "DOC"


class Document(BaseModel):
    """Represents any Document.
    A document is any piece of text that can be embedded and send as a document to a LLM.
    Documents may have extra metadata for display/search.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda : uuid.uuid4().hex)
    title: str = ""
    text: str = ""
    type: DocType = DocType.DOCUMENT
    labels: list[str] = []
    summary: Optional[str] = None
    labels: Optional[list[str]] = None
    similar_documents: Optional[list[str]] = None
    vector: Optional[numpy.ndarray] = None

    def to_markdown(self):
        """Markdown serialization."""
        title = f"{self.title}" if self.title else ""
        return f"**{title}**<br>**doc {self.id}**<br><br>{self.text}"
    
CONTEXT_TAG = "CONTEXT"


class SimilarDocument(BaseModel):
    document: Document
    score: float

class Context(BaseModel):
    """A Context groups all the information required to chat with a LLM.
    
        Args:
            name: name of the context for display
            documents: list of documents the llms can use as background info for its responses
            prompt: the system prompt to use.
            message_history: the history of interactions with the user. The first message (system prompt) is excluded.
            created: when the context has been created
    """

    id: str = Field(default_factory=lambda : uuid.uuid4().hex)
    # TODO copy value from id by default, rather than generating another uuid.
    name: str = Field(default_factory=lambda : uuid.uuid4().hex)
    documents: dict[str,Document] = {}
    prompt: str = PROMPT_CONVERSE
    message_history: list[Message] = []
    created: datetime.datetime = Field(default_factory=datetime.datetime.now)
    summary: Optional[str] = None
    labels: Optional[list[str]] = None
    
    def to_markdown(self, prompt: str = ""):
        """Markdown string representation of the context."""
        records = "<br>".join([f"<{DOCUMENT_TAG}>{record.to_markdown()}</{DOCUMENT_TAG}>" for record in self.documents.values()])
        if prompt == "":
            prompt = self.prompt
        return f"""{prompt} <{CONTEXT_TAG}>{records}</{CONTEXT_TAG}>"""

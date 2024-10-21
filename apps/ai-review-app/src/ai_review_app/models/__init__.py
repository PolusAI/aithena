"""Module for defining the models for the dashboard."""

from .old_context import ContextPart
from .old_document import OldAuthor, OldDocument, OldDocumentCollection
from .selection import Selection

__all__ = ["OldDocument", "OldAuthor", "OldDocumentCollection", "ContextPart", "Selection"]

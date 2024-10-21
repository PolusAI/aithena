"""Selection model."""

import uuid
from pathlib import Path
from typing import Optional, Union

from pydantic import UUID4, BaseModel

from .old_context import ContextPart


class Selection(BaseModel):
    """Base Model for Selection."""

    parts: list[ContextPart]
    id: UUID4 = uuid.uuid4()
    name: Optional[str] = None

    @property
    def titles(self) -> list[str]:
        """Return the titles of the parts."""
        return [part.content.title for part in self.parts if part.type == "article"]

    @property
    def user_input(self) -> str:
        """Return the user input."""
        return " ".join(
            [part.content for part in self.parts if part.type == "user_input"]
        )

    @classmethod
    def from_json(cls, file: Union[str, Path]) -> "Selection":
        """Load a selection from a json file."""
        with open(file, "r", encoding="utf-8") as f:
            data = f.read()
        return cls.model_validate_json(data)

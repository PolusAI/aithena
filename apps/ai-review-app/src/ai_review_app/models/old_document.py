"""Base Model for Document."""

from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, field_validator
from polus.aithena.common.logger import get_logger
from qdrant_client.http.models.models import Record

logger = get_logger(__name__)

class OldAuthor(BaseModel):
    """Base Model for Author."""
    name: str
    forenames: Optional[str] = None
    suffix: Optional[str] = None
    affiliation: Optional[str] = None

    @classmethod
    def from_record(cls, doc: dict) -> "OldAuthor":
        """Create an `Author` from a dictionary coming from a `Record`."""
        affiliation_ = doc.get("affiliation", None)
        if isinstance(affiliation_, list):
            if len(affiliation_) == 0:
                affiliation_ = None
            else:
                affiliation_ = " ".join(affiliation_)

        return cls(
            name=doc.get("keyname"),
            forenames=doc.get("forenames"),
            suffix=doc.get("suffix"),
            affiliation=affiliation_,
        )


class OldDocument(BaseModel):
    """Base Model for Document."""

    record_id: str
    abstract: str
    title: str
    authors: list[OldAuthor]
    categories: list[str]
    comments: str
    created: datetime
    doi: str
    document_id: str
    journal: str
    updated: datetime
    vector: list[float]

    @classmethod
    def from_record(cls, record: Record) -> "OldDocument":
        """Create a `Document` from a `Record`."""
        return cls(
            record_id=record.id,
            abstract=record.payload.get("abstract")[0],
            title=record.payload.get("title")[0],
            authors=[
                OldAuthor.from_record(x["author"][0])
                for x in record.payload.get("authors")
            ],
            categories=record.payload.get("categories"),
            comments=record.payload.get("comments")[0],
            created=datetime.strptime(record.payload.get("created")[0], "%m/%d/%Y"),
            doi=record.payload.get("doi")[0],
            document_id=record.payload.get("id")[0],
            journal=record.payload.get("journal_ref")[0],
            updated=datetime.strptime(record.payload.get("updated")[0], "%m/%d/%Y"),
            vector=record.vector,
        )

    @property
    def authors_str(self) -> str:
        """Return authors as a string."""
        return ", ".join([x.name for x in self.authors])

    def __hash__(self):
        return hash(self.record_id) + hash(self.document_id) + hash(self.title)


class OldDocumentCollection(BaseModel):
    """Base Model for DocumentCollection."""

    documents: list[OldDocument]
    collection_name: str

    @field_validator("documents", mode="before")
    @classmethod
    def validate_initial_list(cls, value: Any):
        """Ensure that the documents are of the correct type."""
        if all(isinstance(x, Record) for x in value):
            return [OldDocument.from_record(x) for x in value]
        if all(isinstance(x, OldDocument) for x in value):
            return value
        raise ValueError("documents must be a list of Document or Record")

    @property
    def df(self):  # TODO: improve name
        """Return the documents as a DataFrame of title and authors."""
        data = [{"title": x.title, "authors": x.authors_str} for x in self.documents]
        return pd.DataFrame(data)

    @property
    def embeddings(self):
        """Return `np.ndarray` of vector embeddings in the collection."""
        return np.array([x.vector for x in self.documents])

    def __getitem__(self, idx):
        """Return the document at the given index."""
        return self.documents[idx]

    def __len__(self):
        """Return the number of documents in the collection."""
        return len(self.documents)

    def __iter__(self):
        """Iterate over the documents in the collection."""
        return iter(self.documents)

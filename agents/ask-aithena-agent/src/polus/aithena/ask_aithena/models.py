from functools import cached_property
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
import orjson


class Document(BaseModel):
    """Document retrieved from the database."""

    id: str = Field(..., description="The id of the document")
    content: str = Field(..., description="The content of the document")
    year: str | int = Field(..., description="The publication year of the document")
    doi: str = Field(
        ..., description="The DOI of the document, empty string if unknown"
    )
    authors: List[str | None] = Field(
        ..., description="The authors of the document, can be empty list if unknown"
    )
    title: str = Field(..., description="The title of the document")
    similarity_score: float = Field(..., description="The similarity score of the document from PGVector")

    def to_context(self, n: int, reason: Optional[str] = None) -> str:
        """Convert document to context string format."""
        context_string = (
            f"<doc>\n<index>{n+1}</index>\n<content>{self.content}</content>\n"
        )
        if reason:
            context_string += f"<reason>{reason}</reason>\n"
        context_string += "</doc>\n"
        return context_string

    def to_reference(self, score: Optional[float] = None, include_abstract: bool = False) -> Dict[str, Any]:
        """Convert document to reference dictionary format for frontend rendering."""
        if include_abstract:
            return {
                "title": self.title,
                "authors": self.authors,
                "year": self.year,
                "doi": self.doi,
                "id": self.id,
                "score": score if score is not None else self.similarity_score,
                "abstract": self.content,
            }
        else:
            return {
                "title": self.title,
                "authors": self.authors,
                "year": self.year,
                "doi": self.doi,
                "id": self.id,
                "score": score if score is not None else self.similarity_score,
            }

    @classmethod
    def from_work(cls, work: dict) -> "Document":
        """Convert work to document."""
        if work["authorships"] is None:
            authors_ = []
        else:
            authors_ = [
                author["display_name"]
                for author in work["authorships"]
                if author["display_name"] is not None
            ]

        return cls(
            id=work["id"],
            content=work["abstract"],
            year=work["publication_year"],
            doi=work["doi"] or "",
            authors=authors_,
            title=work["title"],
            similarity_score=work["similarity_score"],
        )

    # sometimes, the title is None, so we need to validate it
    @field_validator("title", mode="before")
    def validate_title(cls, v):
        if v is None:
            return "No title provided"
        return v


class Context(BaseModel):
    """Context containing retrieved documents."""

    documents: List[Document] = Field(default_factory=list)
    reranked_indices: Optional[list[int]] = Field(
        default=None,
        description="The indices of the documents in the original list of documents, sorted by relevance to the query.",
    )
    reranked_scores: Optional[list[float]] = Field(
        default=None,
        description="The relevance scores of the documents in the reranked list, from most relevant to least relevant.",
    )
    reranked_reasons: Optional[list[str]] = Field(
        default=None,
        description="The reasons for the relevance scores of the documents in the reranked list.",
    )

    def to_llm_context(self) -> str:
        """Convert context to a format suitable for the LLM."""
        if self.reranked_reasons is None:
            docs = "\n".join(
                [doc.to_context(n) for n, doc in enumerate(self._documents())]
            )
        else:
            docs = "\n".join(
                [
                    doc.to_context(n, reason=self.reranked_reasons[n])
                    for n, doc in enumerate(self._documents())
                ]
            )
        return f"<context>\n{docs}\n</context>"

    def to_references(self) -> str:
        """Convert documents to a JSON reference list for the frontend."""
        references = []
        for i, doc in enumerate(self._documents()):
            ref_data = doc.to_reference(
                score=(
                    self.reranked_scores[i]
                    if self.reranked_scores is not None
                    else None
                )
            )
            # Add the index (1-based) to each reference
            ref_data["index"] = i + 1
            references.append(ref_data)

        # Return a JSON string that the frontend can parse
        return orjson.dumps(references).decode("utf-8")
    
    def to_list_for_mcp(self) -> list[dict]:
        """Convert context to a list of dictionaries with abstracts for MCP."""
        references = []
        for i, doc in enumerate(self._documents()):
            ref_data = doc.to_reference(
                score=(
                    self.reranked_scores[i]
                    if self.reranked_scores is not None
                    else None
                ),
                include_abstract=True,
            )
            # Add the index (1-based) to each reference
            ref_data["index"] = i + 1
            references.append(ref_data)

        # Return a JSON string that the frontend can parse
        return references

    def to_works_for_reranker(self) -> str:
        """Convert context to works for reranker string."""
        return "".join(self.works_for_reranker)

    @property
    def works_for_reranker(self) -> list[str]:
        """Context as a list of works for reranker."""
        return [
            f"<work><index>{n}</index>{doc.model_dump_json(include={'title', 'content'})}</work>"
            for n, doc in enumerate(
                self.documents
            )  # NOT _documents because it is for reranker
        ]

    @classmethod
    def from_works(cls, works: List[dict]) -> "Context":
        """Convert works to context."""
        return cls(documents=[Document.from_work(work) for work in works])

    def _documents(self) -> List[Document]:
        """Private method to get documents list."""
        if self.reranked_indices is None:
            return self.documents
        return self.reranked_documents

    @cached_property
    def reranked_documents(self) -> List[Document]:
        """Documents sorted by relevance to the query."""
        if self.reranked_indices is None:
            return self.documents
        return [self.documents[i] for i in self.reranked_indices]

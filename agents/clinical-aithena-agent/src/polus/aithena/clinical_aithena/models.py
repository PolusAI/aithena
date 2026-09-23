import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector  # type: ignore
from pydantic import BaseModel, Field
from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field as SQLField
from sqlmodel import Relationship, SQLModel

if TYPE_CHECKING:
    from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy


class TrialMetadata(BaseModel):
    brief_title: Optional[str] = Field(
        None, description="A brief title of the clinical trial"
    )
    phase: Optional[str] = Field(None, description="The phase of the clinical trial")
    drugs: Optional[str] = Field(
        None, description="String representation of the list of drugs involved"
    )
    drugs_list: Optional[List[str]] = Field(
        default_factory=list, description="List of drugs involved in the trial"
    )
    diseases: Optional[str] = Field(
        None, description="String representation of the list of diseases targeted"
    )
    diseases_list: Optional[List[str]] = Field(
        default_factory=list, description="List of diseases targeted by the trial"
    )
    enrollment: Optional[str] = Field(
        None, description="The enrollment number as a string (e.g. '60.0')"
    )
    inclusion_criteria: Optional[str] = Field(
        None, description="Inclusion criteria text"
    )
    exclusion_criteria: Optional[str] = Field(
        None, description="Exclusion criteria text"
    )
    brief_summary: Optional[str] = Field(
        None, description="A brief summary of the trial"
    )


class Trial(BaseModel):
    id: str = Field(
        ...,
        alias="_id",
        description="The unique identifier for the trial (e.g., NCT number)",
    )
    title: str = Field(..., description="The title of the clinical trial")
    text: str = Field(
        ...,
        description="Full text description of the trial, including summary and criteria",
    )
    metadata: TrialMetadata = Field(
        ..., description="Structured metadata associated with the trial"
    )


class TrialGPTStudy(SQLModel, table=True):
    """
    SQLModel representation of a Clinical Trial for TrialGPT.
    Includes embeddings for semantic search and JSONB for flexible metadata.
    """

    __tablename__ = "trialgpt_study"
    __table_args__ = (
        # HNSW indexes for embeddings
        Index(
            "idx_trialgpt_title_embedding_hnsw",
            "title_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"title_embedding": "vector_cosine_ops"},
        ),
        Index(
            "idx_trialgpt_text_embedding_hnsw",
            "text_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"text_embedding": "vector_cosine_ops"},
        ),
        # GIN index for full-text search (BM25) on text field
        Index(
            "idx_trialgpt_text_gin",
            "text",
            postgresql_using="gin",
            postgresql_ops={"text": "gin_trgm_ops"},
        ),
        # GIN index for JSONB metadata
        Index(
            "idx_trialgpt_metadata_gin",
            "metadata_json",
            postgresql_using="gin",
        ),
    )

    nct_id: str = SQLField(
        primary_key=True, description="The unique NCT identifier"
    )
    title: str = SQLField(description="The title of the clinical trial")
    text: str = SQLField(
        description="Full text description of the trial, including summary and criteria"
    )
    metadata_json: Dict[str, Any] = SQLField(
        sa_column=Column(JSONB), description="Structured metadata (TrialMetadata)"
    )

    # Embeddings (MedCPT produces 768-dimensional embeddings)
    title_embedding: Optional[List[float]] = SQLField(
        default=None, sa_column=Column(Vector(768))
    )
    text_embedding: Optional[List[float]] = SQLField(
        default=None, sa_column=Column(Vector(768))
    )

    # Link to raw CTGovStudy
    ctgov_study_id: Optional[int] = SQLField(
        default=None,
        foreign_key="ctgovstudy.id",
        description="ID of the source CTGovStudy record",
    )
    ctgov_study: Optional["CTGovStudy"] = Relationship()

    def to_pydantic(self) -> Trial:
        """Convert SQLModel instance to Trial Pydantic model."""
        return Trial(
            _id=self.nct_id,
            title=self.title,
            text=self.text,
            metadata=TrialMetadata(**self.metadata_json),
        )

    @classmethod
    def from_pydantic(
        cls,
        trial: Trial,
        ctgov_study_id: Optional[int] = None,
        title_embedding: Optional[List[float]] = None,
        text_embedding: Optional[List[float]] = None,
    ) -> "TrialGPTStudy":
        """Create SQLModel instance from Trial Pydantic model."""
        # Use .dict() for Pydantic v1/v2 compatibility if model_dump is unsafe,
        # but model_dump is preferred for v2.
        # Assuming environment supports v2 given recent dates/tools.
        # If Trial is a pydantic v1 model, we use .dict().
        # We can try/except or just use .dict() if simple dict is needed.
        # TrialMetadata is simple.
        metadata_dict = (
            trial.metadata.model_dump()
            if hasattr(trial.metadata, "model_dump")
            else trial.metadata.dict()
        )

        return cls(
            nct_id=trial.id,
            title=trial.title,
            text=trial.text,
            metadata_json=metadata_dict,
            ctgov_study_id=ctgov_study_id,
            title_embedding=title_embedding,
            text_embedding=text_embedding,
        )

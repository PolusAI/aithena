"""Retrieval modules for clinical trial search."""

from polus.aithena.clinical_aithena.retrieval.bm25_retriever import (
    BM25Retriever,
)
from polus.aithena.clinical_aithena.retrieval.pg_search_retriever import (
    PgSearchRetriever,
)
from polus.aithena.clinical_aithena.retrieval.vector_retriever import (
    VectorRetriever,
)
from polus.aithena.clinical_aithena.retrieval.hybrid_retriever import (
    HybridRetriever,
    WeightedHybridRetriever,
)

__all__ = [
    "BM25Retriever",  # Legacy in-memory implementation
    "PgSearchRetriever",  # RECOMMENDED: TrialGPT-compliant with zero first-query penalty
    "VectorRetriever",
    "HybridRetriever",
    "WeightedHybridRetriever",
]



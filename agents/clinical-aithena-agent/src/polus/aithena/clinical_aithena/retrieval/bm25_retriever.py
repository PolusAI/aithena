"""
BM25-based retrieval for clinical trials.

Provides database-backed BM25 search with in-memory indexing,
replicating TrialGPT's original BM25 approach.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from rank_bm25 import BM25Okapi
from sqlmodel import Session, select

from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.retrieval.tokenizer import (
    tokenize,
    tokenize_trial_for_bm25,
)

logger = logging.getLogger(__name__)


class BM25Retriever:
    """
    BM25-based retrieval for clinical trials.
    
    This class builds an in-memory BM25 index from the database and
    provides efficient retrieval. The index uses weighted fields
    matching TrialGPT's original approach:
    - Title: 3x weight
    - Diseases: 2x weight
    - Text: 1x weight
    
    The index is built lazily on first search and can be refreshed
    as needed when new trials are added.
    
    Example:
        >>> retriever = BM25Retriever(session)
        >>> results = retriever.search("lung cancer treatment", top_n=100)
        >>> for nct_id, score in results:
        ...     print(f"{nct_id}: {score:.4f}")
    """
    
    def __init__(
        self,
        session: Session,
        auto_refresh: bool = False,
    ):
        """
        Initialize BM25 retriever.
        
        Args:
            session: SQLModel database session
            auto_refresh: If True, check for new trials and rebuild index
                         automatically on each search
        """
        self.session = session
        self.auto_refresh = auto_refresh
        
        self._index: Optional[BM25Okapi] = None
        self._nct_ids: Optional[List[str]] = None
        self._tokenized_corpus: Optional[List[List[str]]] = None
        self._index_built_at: Optional[datetime] = None
        self._trial_count: int = 0
    
    def _build_index(self, force: bool = False) -> None:
        """
        Build BM25 index from database trials.
        
        Fetches all TrialGPTStudy records and creates a weighted
        tokenized corpus for BM25 indexing.
        
        Args:
            force: If True, rebuild even if index already exists
        """
        if self._index is not None and not force:
            logger.debug("BM25 index already built, skipping")
            return
        
        logger.info("Building BM25 index from database...")
        start_time = datetime.now()
        
        # Fetch all trials from database
        # Note: We only need nct_id, title, text, and metadata_json for BM25
        # This avoids issues with VECTOR columns in test environments
        statement = select(
            TrialGPTStudy.nct_id,
            TrialGPTStudy.title,
            TrialGPTStudy.text,
            TrialGPTStudy.metadata_json,
        )
        rows = self.session.exec(statement).all()
        
        if not rows:
            logger.warning("No trials found in database for BM25 indexing")
            self._index = None
            self._nct_ids = []
            self._tokenized_corpus = []
            self._trial_count = 0
            return
        
        tokenized_corpus = []
        nct_ids = []
        
        for row in rows:
            # Unpack the row tuple
            nct_id, title, text, metadata_json = row
            
            # metadata_json might be a string (from DuckDB) or dict (from PostgreSQL)
            import orjson
            if isinstance(metadata_json, str):
                metadata = orjson.loads(metadata_json)
            else:
                metadata = metadata_json
            
            # Tokenize with weighting: 3x title, 2x diseases, 1x text
            tokens = tokenize_trial_for_bm25(
                title=title,
                diseases_list=metadata.get('diseases_list', []),
                text=text,
            )
            
            tokenized_corpus.append(tokens)
            nct_ids.append(nct_id)
        
        # Build BM25 index
        self._index = BM25Okapi(tokenized_corpus)
        self._nct_ids = nct_ids
        self._tokenized_corpus = tokenized_corpus
        self._trial_count = len(rows)
        self._index_built_at = datetime.now()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            "BM25 index built successfully: %d trials indexed in %.2fs",
            self._trial_count,
            elapsed,
        )
    
    def _should_refresh(self) -> bool:
        """
        Check if index should be refreshed.
        
        Returns True if auto_refresh is enabled and the number of
        trials in the database has changed.
        """
        if not self.auto_refresh:
            return False
        
        if self._index is None:
            return True
        
        # Check if trial count has changed
        from sqlalchemy import func
        statement = select(func.count(TrialGPTStudy.nct_id))
        current_count = self.session.exec(statement).one()
        
        if current_count != self._trial_count:
            logger.info(
                "Trial count changed (%d -> %d), refreshing BM25 index",
                self._trial_count,
                current_count,
            )
            return True
        
        return False
    
    def search(
        self,
        query: str,
        top_n: int = 100,
    ) -> List[Tuple[str, float]]:
        """
        Search for trials using BM25.
        
        Args:
            query: Search query string
            top_n: Number of top results to return
            
        Returns:
            List of (nct_id, score) tuples, sorted by score descending
            
        Example:
            >>> results = retriever.search("lung cancer", top_n=10)
            >>> for nct_id, score in results[:3]:
            ...     print(f"{nct_id}: {score:.4f}")
            NCT12345678: 15.4321
            NCT87654321: 12.8765
            NCT11111111: 10.2345
        """
        # Check if we need to build or refresh the index
        if self._should_refresh() or self._index is None:
            self._build_index(force=True)
        
        # If still no index, return empty results
        if self._index is None or not self._nct_ids:
            logger.warning("No BM25 index available, returning empty results")
            return []
        
        # Tokenize query
        query_tokens = tokenize(query)
        
        if not query_tokens:
            logger.warning("Query tokenized to empty list: %s", query)
            return []
        
        # Get BM25 scores for all documents
        scores = self._index.get_scores(query_tokens)
        
        # Create list of (nct_id, score) tuples
        results = list(zip(self._nct_ids, scores))
        
        # Sort by score descending and take top N
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_n]
        
        logger.debug(
            "BM25 search for '%s' returned %d results (top score: %.4f)",
            query,
            len(results),
            results[0][1] if results else 0.0,
        )
        
        return results
    
    def search_multiple(
        self,
        queries: List[str],
        top_n: int = 100,
    ) -> List[List[Tuple[str, float]]]:
        """
        Search for multiple queries (batch processing).
        
        This is useful for processing multiple patient conditions
        or keywords at once.
        
        Args:
            queries: List of search query strings
            top_n: Number of top results to return per query
            
        Returns:
            List of result lists, one per query
            
        Example:
            >>> queries = ["lung cancer", "diabetes", "hypertension"]
            >>> all_results = retriever.search_multiple(queries, top_n=50)
            >>> for i, results in enumerate(all_results):
            ...     print(f"Query {i+1}: {len(results)} results")
        """
        return [self.search(query, top_n=top_n) for query in queries]
    
    def refresh_index(self) -> None:
        """
        Force refresh the BM25 index.
        
        This rebuilds the index from the current database state.
        Useful when you know new trials have been added.
        """
        logger.info("Forcing BM25 index refresh...")
        self._build_index(force=True)
    
    def get_stats(self) -> dict:
        """
        Get statistics about the BM25 index.
        
        Returns:
            Dictionary with index statistics
        """
        return {
            "index_built": self._index is not None,
            "trial_count": self._trial_count,
            "index_built_at": (
                self._index_built_at.isoformat()
                if self._index_built_at
                else None
            ),
            "auto_refresh": self.auto_refresh,
        }


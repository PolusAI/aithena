"""
BM25-based retrieval using ParadeDB's pg_search extension.

Provides database-native BM25 search with zero first-query penalty,
replacing the in-memory rank_bm25 implementation.
"""

import logging
from typing import List, Tuple

from sqlalchemy import text
from sqlmodel import Session

logger = logging.getLogger(__name__)


class PgSearchRetriever:
    """
    BM25-based retrieval using ParadeDB's pg_search extension.
    
    This class provides efficient BM25 search using PostgreSQL's native
    pg_search extension (from ParadeDB). Unlike in-memory solutions,
    this approach:
    - Has zero first-query penalty (no index building needed)
    - Automatically updates with data changes
    - Scales better for large datasets
    - Uses native PostgreSQL BM25 implementation
    
    Example:
        >>> retriever = PgSearchRetriever(session)
        >>> results = retriever.search("lung cancer treatment", top_n=100)
        >>> for nct_id, score in results:
        ...     print(f"{nct_id}: {score:.4f}")
    """
    
    def __init__(self, session: Session):
        """
        Initialize pg_search retriever.
        
        Args:
            session: SQLModel database session
        """
        self.session = session
    
    def search(
        self,
        query: str,
        top_n: int = 100,
    ) -> List[Tuple[str, float]]:
        """
        Search for trials using BM25 via pg_search with TrialGPT field weighting.
        
        Implements the TrialGPT weighting scheme:
        - Title: 3x boost
        - Diseases (metadata): 2x boost  
        - Text: 1x boost (no multiplier)
        
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
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        try:
            # Use pg_search's boost() function to replicate TrialGPT field weighting
            # paradedb.boolean(should => ...) combines multiple field searches
            # paradedb.boost(factor, query) multiplies score by factor
            # paradedb.match() does bag-of-words matching (default OR across tokens),
            # unlike phrase_prefix which requires sequential token matches.
            # This matches TrialGPT's original BM25 approach and dramatically
            # improves recall.
            sql = text("""
                SELECT 
                    nct_id,
                    paradedb.score(nct_id) as score
                FROM trialgpt_study
                WHERE nct_id @@@ paradedb.boolean(
                    should => ARRAY[
                        paradedb.boost(3.0, paradedb.match('title', CAST(:query AS text))),
                        paradedb.boost(2.0, paradedb.match('metadata_json', CAST(:query AS text))),
                        paradedb.match('text', CAST(:query AS text))
                    ]
                )
                ORDER BY score DESC
                LIMIT :top_n
            """)
            
            result = self.session.execute(
                sql,
                {"query": query, "top_n": top_n}
            )
            
            results = [(row.nct_id, float(row.score)) for row in result]
            
            logger.debug(
                "BM25 search for '%s' returned %d results (top score: %.4f)",
                query,
                len(results),
                results[0][1] if results else 0.0,
            )
            
            return results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            # Fallback to empty results rather than crashing
            return []
    
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
    
    def get_stats(self) -> dict:
        """
        Get statistics about the BM25 index.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            # Query pg_search index statistics
            sql = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
                FROM pg_indexes
                WHERE tablename = 'trialgpt_study'
                AND indexdef LIKE '%bm25%'
            """)
            
            result = self.session.execute(sql)
            row = result.fetchone()
            
            if row:
                return {
                    "index_name": row.indexname,
                    "index_size": row.index_size,
                    "table": row.tablename,
                    "schema": row.schemaname,
                    "engine": "pg_search (ParadeDB)",
                }
            else:
                return {
                    "index_name": None,
                    "error": "BM25 index not found",
                }
                
        except Exception as e:
            logger.error(f"Failed to get BM25 stats: {e}")
            return {"error": str(e)}

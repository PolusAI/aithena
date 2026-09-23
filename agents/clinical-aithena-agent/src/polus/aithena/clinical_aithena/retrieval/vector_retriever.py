"""
Vector-based retrieval for clinical trials using MedCPT embeddings.

Provides pgvector-backed semantic search with MedCPT-Query-Encoder,
replicating TrialGPT's vector retrieval approach.
"""

import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlmodel import Session

from polus.aithena.clinical_aithena.embeddings import MedCPTService

logger = logging.getLogger(__name__)


class VectorRetriever:
    """
    Vector-based retrieval for clinical trials using MedCPT embeddings.
    
    This class uses MedCPT-Query-Encoder to encode patient queries and
    searches the database using pgvector's cosine similarity operator.
    Matches TrialGPT's original vector search approach.
    
    The retriever supports:
    - Single and batch query encoding
    - Multi-keyword queries with aggregation
    - Result deduplication and score merging
    - Configurable top-K results
    
    Example:
        >>> retriever = VectorRetriever(session, medcpt_service)
        >>> results = retriever.search("lung cancer treatment", top_k=100)
        >>> for nct_id, score in results[:5]:
        ...     print(f"{nct_id}: {score:.4f}")
    """
    
    def __init__(
        self,
        session: Session,
        medcpt_service: Optional[MedCPTService] = None,
    ):
        """
        Initialize vector retriever.
        
        Args:
            session: SQLModel database session
            medcpt_service: MedCPT embedding service (creates new if not provided)
        """
        self.session = session
        self.medcpt_service = medcpt_service or MedCPTService()
        
        logger.info("Initialized VectorRetriever with MedCPT service")
    
    def search(
        self,
        query: str,
        top_k: int = 100,
        embedding_field: str = "text_embedding",
    ) -> List[Tuple[str, float]]:
        """
        Search for trials using vector similarity.
        
        Encodes the query using MedCPT-Query-Encoder and searches the
        database for the top-K most similar trials using cosine similarity.
        
        Args:
            query: Patient query string or condition
            top_k: Number of top results to return
            embedding_field: Which embedding field to search
                           ('text_embedding' or 'title_embedding')
            
        Returns:
            List of (nct_id, similarity_score) tuples, sorted by score descending
            
        Example:
            >>> results = retriever.search("stage III lung cancer", top_k=50)
            >>> print(f"Top result: {results[0][0]} with score {results[0][1]:.4f}")
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to vector search")
            return []
        
        # Encode query using MedCPT-Query-Encoder
        try:
            query_embedding = self.medcpt_service.encode_query(query)
        except Exception as e:
            logger.error(f"Failed to encode query '{query}': {e}")
            return []
        
        # Query database using pgvector's cosine similarity operator (<=>)
        # Note: pgvector's <=> operator returns distance (0 = identical, 2 = opposite)
        # We convert to similarity score: similarity = 1 - (distance / 2)
        sql = text(f"""
            SELECT 
                nct_id,
                1 - ({embedding_field} <=> CAST(:query_embedding AS vector)) AS similarity
            FROM trialgpt_study
            WHERE {embedding_field} IS NOT NULL
            ORDER BY {embedding_field} <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)
        
        try:
            # Convert list to string format for pgvector: "[0.1,0.2,...]"
            embedding_str = str(query_embedding)
            result = self.session.execute(
                sql,
                {"query_embedding": embedding_str, "top_k": top_k}
            )
            
            # Convert to list of tuples
            results = [(row[0], float(row[1])) for row in result]
            
            logger.debug(
                f"Vector search for '{query}' returned {len(results)} results "
                f"(top score: {results[0][1]:.4f})" if results else 
                f"Vector search for '{query}' returned no results"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def search_batch(
        self,
        queries: List[str],
        top_k: int = 100,
        embedding_field: str = "text_embedding",
    ) -> List[List[Tuple[str, float]]]:
        """
        Search for multiple queries (batch processing).
        
        This is useful for processing multiple patient conditions at once.
        Each query is processed independently.
        
        Args:
            queries: List of query strings
            top_k: Number of top results to return per query
            embedding_field: Which embedding field to search
            
        Returns:
            List of result lists, one per query
            
        Example:
            >>> queries = ["lung cancer", "diabetes", "hypertension"]
            >>> all_results = retriever.search_batch(queries, top_k=50)
            >>> for i, results in enumerate(all_results):
            ...     print(f"Query {i+1}: {len(results)} results")
        """
        return [
            self.search(query, top_k=top_k, embedding_field=embedding_field)
            for query in queries
        ]
    
    def search_multi_conditions(
        self,
        conditions: List[str],
        top_k: int = 100,
        embedding_field: str = "text_embedding",
        aggregation_method: str = "weighted_rrf",
    ) -> List[Tuple[str, float]]:
        """
        Search with multiple conditions and aggregate results.
        
        This matches TrialGPT's approach of handling multiple patient conditions.
        Results are aggregated using weighted reciprocal rank fusion, where
        earlier conditions (higher priority) receive higher weights.
        
        Args:
            conditions: List of patient conditions/keywords
            top_k: Number of top results to return from each condition search
            embedding_field: Which embedding field to search
            aggregation_method: How to aggregate results:
                - 'weighted_rrf': Weighted reciprocal rank fusion (default)
                - 'max': Take maximum score across conditions
                - 'sum': Sum scores across conditions
            
        Returns:
            List of (nct_id, aggregated_score) tuples, sorted by score descending
            
        Example:
            >>> conditions = ["lung cancer stage III", "EGFR mutation", "ECOG 0-1"]
            >>> results = retriever.search_multi_conditions(conditions, top_k=100)
            >>> print(f"Top trial: {results[0][0]} with score {results[0][1]:.4f}")
        """
        if not conditions:
            logger.warning("No conditions provided to multi-condition search")
            return []
        
        # Search for each condition
        all_results = self.search_batch(
            conditions,
            top_k=top_k,
            embedding_field=embedding_field
        )
        
        # Aggregate results
        nct_id_to_score: Dict[str, float] = {}
        
        for condition_idx, condition_results in enumerate(all_results):
            # Condition weighting: 1/(condition_idx + 1)
            # Earlier conditions (higher priority) get higher weights
            condition_weight = 1.0 / (condition_idx + 1)
            
            for rank, (nct_id, similarity) in enumerate(condition_results):
                if nct_id not in nct_id_to_score:
                    nct_id_to_score[nct_id] = 0.0
                
                if aggregation_method == "weighted_rrf":
                    # Weighted reciprocal rank fusion
                    # Uses similarity score as additional weight
                    nct_id_to_score[nct_id] += (
                        similarity * condition_weight / (rank + 1)
                    )
                elif aggregation_method == "max":
                    # Take maximum score
                    nct_id_to_score[nct_id] = max(
                        nct_id_to_score[nct_id],
                        similarity * condition_weight
                    )
                elif aggregation_method == "sum":
                    # Sum scores
                    nct_id_to_score[nct_id] += similarity * condition_weight
        
        # Sort by aggregated score
        aggregated_results = sorted(
            nct_id_to_score.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(
            f"Multi-condition search with {len(conditions)} conditions "
            f"returned {len(aggregated_results)} unique trials"
        )
        
        return aggregated_results
    
    def get_stats(self) -> dict:
        """
        Get statistics about the vector index.
        
        Returns:
            Dictionary with index statistics
        """
        # Count trials with embeddings
        sql = text("""
            SELECT 
                COUNT(*) FILTER (WHERE text_embedding IS NOT NULL) as text_count,
                COUNT(*) FILTER (WHERE title_embedding IS NOT NULL) as title_count,
                COUNT(*) as total_trials
            FROM trialgpt_study
        """)
        
        try:
            result = self.session.execute(sql)
            row = result.fetchone()
            
            return {
                "total_trials": row[2],
                "trials_with_text_embedding": row[0],
                "trials_with_title_embedding": row[1],
                "embedding_dimension": 768,
                "embedding_model": "MedCPT-Query-Encoder / MedCPT-Article-Encoder",
            }
        except Exception as e:
            logger.error(f"Failed to get vector index stats: {e}")
            return {
                "error": str(e)
            }


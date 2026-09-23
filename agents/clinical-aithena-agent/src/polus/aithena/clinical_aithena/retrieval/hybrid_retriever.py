"""
Hybrid retrieval combining BM25 and vector search with reciprocal rank fusion.

Implements TrialGPT's hybrid fusion approach for clinical trial retrieval,
combining keyword-based BM25 search with semantic vector search.
"""

import logging
from typing import Dict, List, Optional, Tuple

from sqlmodel import Session

from polus.aithena.clinical_aithena.embeddings import MedCPTService
from polus.aithena.clinical_aithena.retrieval.pg_search_retriever import PgSearchRetriever
from polus.aithena.clinical_aithena.retrieval.vector_retriever import VectorRetriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid retrieval combining BM25 and vector search with reciprocal rank fusion.
    
    This class implements TrialGPT's hybrid retrieval approach, which combines:
    - BM25 keyword-based search (using ParadeDB's pg_search extension)
    - MedCPT vector-based semantic search (using pgvector)
    
    Results are fused using reciprocal rank fusion (RRF) with the formula:
        score = (1 / (rank + k)) * (1 / (condition_idx + 1))
    
    Where:
    - k: smoothing constant (default 20, from TrialGPT)
    - rank: position in retrieval results (0-indexed)
    - condition_idx: condition priority (0-indexed, earlier = higher priority)
    
    Example:
        >>> retriever = HybridRetriever(session)
        >>> conditions = ["lung cancer stage III", "EGFR mutation"]
        >>> results = retriever.search(conditions, top_n=100)
        >>> for nct_id, score in results[:5]:
        ...     print(f"{nct_id}: {score:.4f}")
    """
    
    def __init__(
        self,
        session: Session,
        medcpt_service: Optional[MedCPTService] = None,
        bm25_retriever: Optional[PgSearchRetriever] = None,
        vector_retriever: Optional[VectorRetriever] = None,
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            session: SQLModel database session
            medcpt_service: MedCPT embedding service (creates new if not provided)
            bm25_retriever: PgSearch retriever instance (creates new if not provided)
            vector_retriever: Vector retriever instance (creates new if not provided)
        """
        self.session = session
        self.medcpt_service = medcpt_service or MedCPTService()
        
        # Initialize retrievers
        self.bm25_retriever = bm25_retriever or PgSearchRetriever(session)
        self.vector_retriever = vector_retriever or VectorRetriever(
            session, self.medcpt_service
        )
        
        logger.info("Initialized HybridRetriever with pg_search (BM25) and Vector retrievers")
    
    def search(
        self,
        conditions: List[str],
        top_n: int = 100,
        rrf_k: int = 20,
        bm25_weight: float = 1.0,
        vector_weight: float = 1.0,
        retrieval_depth: Optional[int] = None,
    ) -> List[Tuple[str, float]]:
        """
        Search using hybrid fusion of BM25 and vector retrieval.

        This implements TrialGPT's hybrid retrieval approach:
        1. For each condition, retrieve results from BM25 and vector
        2. Apply reciprocal rank fusion (RRF) to each result set
        3. Weight and aggregate scores across conditions
        4. Return top-N fused results

        Args:
            conditions: List of patient conditions/keywords
            top_n: Maximum number of final fused results to return
            rrf_k: Smoothing constant for RRF (default 20, from TrialGPT)
            bm25_weight: Weight for BM25 results (0.0 to disable)
            vector_weight: Weight for vector results (0.0 to disable)
            retrieval_depth: Number of results to retrieve **per method
                per condition**.  Defaults to ``top_n`` when *None*.
                TrialGPT uses 2000 per condition; higher values improve
                recall at the cost of latency.

        Returns:
            List of (nct_id, fused_score) tuples, sorted by score descending

        Example:
            >>> conditions = ["lung cancer", "stage III", "EGFR mutation"]
            >>> results = retriever.search(
            ...     conditions,
            ...     top_n=100,
            ...     retrieval_depth=2000,
            ... )
        """
        if not conditions:
            logger.warning("No conditions provided to hybrid search")
            return []

        if bm25_weight <= 0 and vector_weight <= 0:
            logger.warning(
                "Both BM25 and vector weights are zero or negative"
            )
            return []

        depth = retrieval_depth if retrieval_depth is not None else top_n

        logger.info(
            f"Hybrid search with {len(conditions)} conditions "
            f"(depth: {depth}, top_n: {top_n}, "
            f"BM25 wt: {bm25_weight}, Vec wt: {vector_weight}, "
            f"RRF k: {rrf_k})"
        )

        # Dictionary to accumulate scores
        nct_id_to_score: Dict[str, float] = {}

        # Process each condition
        for condition_idx, condition in enumerate(conditions):
            # Condition weighting: 1 / (condition_idx + 1)
            # Earlier conditions (higher priority) get higher weights
            condition_weight = 1.0 / (condition_idx + 1)

            logger.debug(
                f"Processing condition {condition_idx + 1}/"
                f"{len(conditions)}: '{condition}' "
                f"(weight: {condition_weight:.3f})"
            )

            # BM25 retrieval
            if bm25_weight > 0:
                bm25_results = self.bm25_retriever.search(
                    condition, top_n=depth,
                )

                # Apply RRF to BM25 results
                for rank, (nct_id, _) in enumerate(bm25_results):
                    if nct_id not in nct_id_to_score:
                        nct_id_to_score[nct_id] = 0.0

                    rrf_score = (
                        (1.0 / (rank + rrf_k)) * condition_weight
                    )
                    nct_id_to_score[nct_id] += (
                        bm25_weight * rrf_score
                    )

            # Vector retrieval
            if vector_weight > 0:
                vector_results = self.vector_retriever.search(
                    condition, top_k=depth,
                )

                # Apply RRF to vector results
                for rank, (nct_id, _) in enumerate(vector_results):
                    if nct_id not in nct_id_to_score:
                        nct_id_to_score[nct_id] = 0.0

                    rrf_score = (
                        (1.0 / (rank + rrf_k)) * condition_weight
                    )
                    nct_id_to_score[nct_id] += (
                        vector_weight * rrf_score
                    )

        # Sort by fused score (descending) and limit to top_n
        fused_results = sorted(
            nct_id_to_score.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        if fused_results:
            logger.info(
                f"Hybrid search returned {len(fused_results)} unique "
                f"trials (top score: {fused_results[0][1]:.4f})"
            )
        else:
            logger.info("Hybrid search returned no results")

        return fused_results
    
    def search_bm25_only(
        self,
        conditions: List[str],
        top_n: int = 100,
        retrieval_depth: Optional[int] = None,
    ) -> List[Tuple[str, float]]:
        """
        Search using only BM25 (for comparison/ablation studies).

        Args:
            conditions: List of patient conditions/keywords
            top_n: Number of top results to return
            retrieval_depth: Per-condition retrieval limit

        Returns:
            List of (nct_id, score) tuples
        """
        return self.search(
            conditions,
            top_n=top_n,
            bm25_weight=1.0,
            vector_weight=0.0,
            retrieval_depth=retrieval_depth,
        )

    def search_vector_only(
        self,
        conditions: List[str],
        top_n: int = 100,
        retrieval_depth: Optional[int] = None,
    ) -> List[Tuple[str, float]]:
        """
        Search using only vector search (for comparison/ablation).

        Args:
            conditions: List of patient conditions/keywords
            top_n: Number of top results to return
            retrieval_depth: Per-condition retrieval limit

        Returns:
            List of (nct_id, score) tuples
        """
        return self.search(
            conditions,
            top_n=top_n,
            bm25_weight=0.0,
            vector_weight=1.0,
            retrieval_depth=retrieval_depth,
        )
    
    def compare_methods(
        self,
        conditions: List[str],
        top_n: int = 100,
        rrf_k: int = 20,
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Compare BM25-only, vector-only, and hybrid retrieval.
        
        Useful for analysis and ablation studies.
        
        Args:
            conditions: List of patient conditions/keywords
            top_n: Number of top results to return
            rrf_k: Smoothing constant for RRF
            
        Returns:
            Dictionary with keys 'bm25', 'vector', and 'hybrid',
            each containing a list of (nct_id, score) tuples
            
        Example:
            >>> results = retriever.compare_methods(["lung cancer"], top_n=50)
            >>> print(f"BM25: {len(results['bm25'])} results")
            >>> print(f"Vector: {len(results['vector'])} results")
            >>> print(f"Hybrid: {len(results['hybrid'])} results")
        """
        return {
            "bm25": self.search_bm25_only(conditions, top_n),
            "vector": self.search_vector_only(conditions, top_n),
            "hybrid": self.search(conditions, top_n, rrf_k),
        }
    
    def get_stats(self) -> dict:
        """
        Get statistics about the hybrid retriever.
        
        Returns:
            Dictionary with retriever statistics
        """
        return {
            "bm25_stats": self.bm25_retriever.get_stats(),
            "vector_stats": self.vector_retriever.get_stats(),
            "hybrid_enabled": True,
        }


class WeightedHybridRetriever(HybridRetriever):
    """
    Hybrid retriever with similarity-weighted RRF.

    This variant uses the actual similarity scores from BM25 and vector
    retrievers as additional weights in the RRF formula, rather than
    treating all results equally within their rank.

    Formula:
        score = similarity * (1/(rank+k)) * (1/(condition_idx+1))

    This can provide better results when similarity scores are
    well-calibrated.
    """

    def search(
        self,
        conditions: List[str],
        top_n: int = 100,
        rrf_k: int = 20,
        bm25_weight: float = 1.0,
        vector_weight: float = 1.0,
        retrieval_depth: Optional[int] = None,
    ) -> List[Tuple[str, float]]:
        """Search using similarity-weighted hybrid fusion."""
        if not conditions:
            return []

        if bm25_weight <= 0 and vector_weight <= 0:
            return []

        depth = retrieval_depth if retrieval_depth is not None else top_n
        nct_id_to_score: Dict[str, float] = {}

        for condition_idx, condition in enumerate(conditions):
            condition_weight = 1.0 / (condition_idx + 1)

            if bm25_weight > 0:
                bm25_results = self.bm25_retriever.search(
                    condition, top_n=depth,
                )
                for rank, (nct_id, sim) in enumerate(bm25_results):
                    if nct_id not in nct_id_to_score:
                        nct_id_to_score[nct_id] = 0.0
                    rrf = (
                        sim
                        * (1.0 / (rank + rrf_k))
                        * condition_weight
                    )
                    nct_id_to_score[nct_id] += bm25_weight * rrf

            if vector_weight > 0:
                vector_results = self.vector_retriever.search(
                    condition, top_k=depth,
                )
                for rank, (nct_id, sim) in enumerate(
                    vector_results,
                ):
                    if nct_id not in nct_id_to_score:
                        nct_id_to_score[nct_id] = 0.0
                    rrf = (
                        sim
                        * (1.0 / (rank + rrf_k))
                        * condition_weight
                    )
                    nct_id_to_score[nct_id] += vector_weight * rrf

        fused_results = sorted(
            nct_id_to_score.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        return fused_results


"""Tests for hybrid retrieval with reciprocal rank fusion."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import JSON
from sqlalchemy.dialects import postgresql
from sqlmodel import Session, create_engine

# Patch JSONB to JSON for DuckDB compatibility
postgresql.JSONB = JSON

from polus.aithena.clinical_aithena.retrieval import (
    HybridRetriever,
    WeightedHybridRetriever,
)


@pytest.fixture
def mock_medcpt_service():
    """Mock MedCPT service."""
    service = Mock()
    service.encode_query.return_value = [0.1] * 768
    return service


@pytest.fixture
def mock_bm25_retriever():
    """Mock BM25 retriever."""
    retriever = Mock()
    # Default: return some results
    retriever.search.return_value = [
        ("NCT00001", 15.5),
        ("NCT00002", 12.3),
        ("NCT00003", 8.7),
    ]
    retriever.get_stats.return_value = {"index_built": True}
    return retriever


@pytest.fixture
def mock_vector_retriever():
    """Mock vector retriever."""
    retriever = Mock()
    # Default: return some results
    retriever.search.return_value = [
        ("NCT00001", 0.95),
        ("NCT00004", 0.85),
        ("NCT00005", 0.75),
    ]
    retriever.get_stats.return_value = {"total_trials": 100}
    return retriever


@pytest.fixture
def in_memory_db():
    """Create an in-memory database for testing."""
    engine = create_engine("duckdb:///:memory:")
    return engine


class TestHybridRetriever:
    """Tests for HybridRetriever."""
    
    def test_initialization(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test retriever initialization."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            assert retriever.session is session
            assert retriever.medcpt_service is mock_medcpt_service
            assert retriever.bm25_retriever is mock_bm25_retriever
            assert retriever.vector_retriever is mock_vector_retriever
    
    def test_initialization_creates_retrievers(self, in_memory_db):
        """Test retriever creates sub-retrievers if not provided."""
        with patch('polus.aithena.clinical_aithena.retrieval.hybrid_retriever.MedCPTService') as mock_service_class:
            with patch('polus.aithena.clinical_aithena.retrieval.hybrid_retriever.PgSearchRetriever') as mock_bm25_class:
                with patch('polus.aithena.clinical_aithena.retrieval.hybrid_retriever.VectorRetriever') as mock_vector_class:
                    mock_service_instance = Mock()
                    mock_bm25_instance = Mock()
                    mock_vector_instance = Mock()
                    
                    mock_service_class.return_value = mock_service_instance
                    mock_bm25_class.return_value = mock_bm25_instance
                    mock_vector_class.return_value = mock_vector_instance
                    
                    with Session(in_memory_db) as session:
                        retriever = HybridRetriever(session)
                        
                        assert retriever.medcpt_service is mock_service_instance
                        assert retriever.bm25_retriever is mock_bm25_instance
                        assert retriever.vector_retriever is mock_vector_instance
    
    def test_search_empty_conditions(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test search with empty conditions."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            results = retriever.search([], top_n=100)
            assert results == []
    
    def test_search_zero_weights(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test search with zero weights."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            results = retriever.search(
                ["test"],
                bm25_weight=0.0,
                vector_weight=0.0
            )
            assert results == []
    
    def test_search_single_condition(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test search with single condition."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            # Set up mock returns
            mock_bm25_retriever.search.return_value = [
                ("NCT00001", 15.0),
                ("NCT00002", 10.0),
            ]
            mock_vector_retriever.search.return_value = [
                ("NCT00001", 0.9),
                ("NCT00003", 0.8),
            ]
            
            results = retriever.search(["lung cancer"], top_n=100)
            
            # Should return results
            assert len(results) > 0
            
            # NCT00001 appears in both, should have highest score
            assert results[0][0] == "NCT00001"
            
            # Results should be sorted by score
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)
    
    def test_search_multiple_conditions(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test search with multiple conditions."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            # Mock different results for different conditions
            mock_bm25_retriever.search.side_effect = [
                [("NCT00001", 15.0), ("NCT00002", 10.0)],  # Condition 1
                [("NCT00003", 12.0), ("NCT00004", 8.0)],   # Condition 2
            ]
            mock_vector_retriever.search.side_effect = [
                [("NCT00001", 0.9), ("NCT00005", 0.7)],   # Condition 1
                [("NCT00002", 0.8), ("NCT00006", 0.6)],   # Condition 2
            ]
            
            results = retriever.search(
                ["lung cancer", "stage III"],
                top_n=100,
                rrf_k=20
            )
            
            # Should aggregate results from all conditions
            assert len(results) > 0
            
            # Should have called retrievers for each condition
            assert mock_bm25_retriever.search.call_count == 2
            assert mock_vector_retriever.search.call_count == 2
    
    def test_search_condition_priority_weighting(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test that earlier conditions receive higher weights."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            # Set up mocks so NCT00001 appears in condition 1 (weight 1.0)
            # and NCT00002 appears in condition 2 (weight 0.5)
            # Both at same rank
            mock_bm25_retriever.search.side_effect = [
                [("NCT00001", 10.0)],  # Condition 1 (weight 1.0)
                [("NCT00002", 10.0)],  # Condition 2 (weight 0.5)
            ]
            mock_vector_retriever.search.side_effect = [
                [],  # No vector results for condition 1
                [],  # No vector results for condition 2
            ]
            
            results = retriever.search(
                ["high_priority", "low_priority"],
                top_n=100,
                rrf_k=20,
                vector_weight=0.0  # Disable vector to simplify test
            )
            
            # NCT00001 should have higher score due to condition priority
            nct_scores = {nct_id: score for nct_id, score in results}
            assert nct_scores["NCT00001"] > nct_scores["NCT00002"]
    
    def test_search_rrf_k_parameter(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test that RRF k parameter affects scores."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            mock_bm25_retriever.search.return_value = [
                ("NCT00001", 10.0),
                ("NCT00002", 5.0),
            ]
            mock_vector_retriever.search.return_value = []
            
            # Test with different k values
            results_k20 = retriever.search(
                ["test"],
                top_n=100,
                rrf_k=20,
                vector_weight=0.0
            )
            
            mock_bm25_retriever.search.return_value = [
                ("NCT00001", 10.0),
                ("NCT00002", 5.0),
            ]
            
            results_k60 = retriever.search(
                ["test"],
                top_n=100,
                rrf_k=60,
                vector_weight=0.0
            )
            
            # Scores should differ with different k values
            # Higher k = smoother fusion (less emphasis on rank)
            assert results_k20[0][1] != results_k60[0][1]
    
    def test_search_configurable_weights(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test configurable BM25 and vector weights."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            mock_bm25_retriever.search.return_value = [("NCT00001", 10.0)]
            mock_vector_retriever.search.return_value = [("NCT00002", 0.9)]
            
            # BM25 only
            results_bm25 = retriever.search(
                ["test"],
                bm25_weight=1.0,
                vector_weight=0.0
            )
            assert results_bm25[0][0] == "NCT00001"
            
            # Reset mocks
            mock_bm25_retriever.search.return_value = [("NCT00001", 10.0)]
            mock_vector_retriever.search.return_value = [("NCT00002", 0.9)]
            
            # Vector only
            results_vector = retriever.search(
                ["test"],
                bm25_weight=0.0,
                vector_weight=1.0
            )
            assert results_vector[0][0] == "NCT00002"
    
    def test_search_bm25_only_helper(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test BM25-only search helper method."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            mock_bm25_retriever.search.return_value = [("NCT00001", 10.0)]
            mock_vector_retriever.search.return_value = [("NCT00002", 0.9)]
            
            results = retriever.search_bm25_only(["test"], top_n=100)
            
            # Should only include BM25 results
            assert len(results) == 1
            assert results[0][0] == "NCT00001"
    
    def test_search_vector_only_helper(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test vector-only search helper method."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            mock_bm25_retriever.search.return_value = [("NCT00001", 10.0)]
            mock_vector_retriever.search.return_value = [("NCT00002", 0.9)]
            
            results = retriever.search_vector_only(["test"], top_n=100)
            
            # Should only include vector results
            assert len(results) == 1
            assert results[0][0] == "NCT00002"
    
    def test_compare_methods(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test method comparison functionality."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            mock_bm25_retriever.search.return_value = [
                ("NCT00001", 10.0),
                ("NCT00002", 5.0),
            ]
            mock_vector_retriever.search.return_value = [
                ("NCT00001", 0.9),
                ("NCT00003", 0.7),
            ]
            
            results = retriever.compare_methods(["test"], top_n=50)
            
            # Should return all three methods
            assert "bm25" in results
            assert "vector" in results
            assert "hybrid" in results
            
            # Each should have results
            assert len(results["bm25"]) > 0
            assert len(results["vector"]) > 0
            assert len(results["hybrid"]) > 0
    
    def test_get_stats(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test getting retriever statistics."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            stats = retriever.get_stats()
            
            # Should include stats from both retrievers
            assert "bm25_stats" in stats
            assert "vector_stats" in stats
            assert "hybrid_enabled" in stats
            assert stats["hybrid_enabled"] is True
    
    def test_top_n_limit(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test that top_n limit is respected."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            # Return many results from sub-retrievers
            mock_bm25_retriever.search.return_value = [
                (f"NCT{i:05d}", 10.0 - i*0.1) for i in range(100)
            ]
            mock_vector_retriever.search.return_value = [
                (f"NCT{i:05d}", 0.9 - i*0.01) for i in range(100)
            ]
            
            results = retriever.search(["test"], top_n=10)
            
            # Should limit to top 10
            assert len(results) <= 10


class TestWeightedHybridRetriever:
    """Tests for WeightedHybridRetriever."""
    
    def test_similarity_weighted_rrf(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test that WeightedHybridRetriever uses similarity scores."""
        with Session(in_memory_db) as session:
            retriever = WeightedHybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            # Set up results with different similarities at same rank
            mock_bm25_retriever.search.return_value = [
                ("NCT00001", 15.0),  # Higher similarity
                ("NCT00002", 5.0),   # Lower similarity
            ]
            mock_vector_retriever.search.return_value = []
            
            results = retriever.search(
                ["test"],
                top_n=100,
                rrf_k=20,
                vector_weight=0.0
            )
            
            # NCT00001 should have higher score due to higher similarity
            nct_scores = {nct_id: score for nct_id, score in results}
            assert nct_scores["NCT00001"] > nct_scores["NCT00002"]
    
    def test_weighted_vs_standard_difference(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test that weighted and standard RRF produce different results."""
        with Session(in_memory_db) as session:
            standard_retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            weighted_retriever = WeightedHybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            # Set up results with varying similarities
            mock_bm25_retriever.search.return_value = [
                ("NCT00001", 15.0),
                ("NCT00002", 10.0),
                ("NCT00003", 5.0),
            ]
            mock_vector_retriever.search.return_value = []
            
            results_standard = standard_retriever.search(
                ["test"],
                top_n=100,
                rrf_k=20,
                vector_weight=0.0
            )
            
            # Reset mock
            mock_bm25_retriever.search.return_value = [
                ("NCT00001", 15.0),
                ("NCT00002", 10.0),
                ("NCT00003", 5.0),
            ]
            
            results_weighted = weighted_retriever.search(
                ["test"],
                top_n=100,
                rrf_k=20,
                vector_weight=0.0
            )
            
            # Scores should differ between standard and weighted
            standard_scores = {nct_id: score for nct_id, score in results_standard}
            weighted_scores = {nct_id: score for nct_id, score in results_weighted}
            
            # Weighted should emphasize high-similarity results more
            assert weighted_scores["NCT00001"] > standard_scores["NCT00001"]


class TestHybridRetrieverValidation:
    """Validation tests for HybridRetriever."""
    
    def test_result_format(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test that results have correct format."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            mock_bm25_retriever.search.return_value = [("NCT00001", 10.0)]
            mock_vector_retriever.search.return_value = [("NCT00002", 0.9)]
            
            results = retriever.search(["test"], top_n=100)
            
            # Verify format
            assert isinstance(results, list)
            for result in results:
                assert isinstance(result, tuple)
                assert len(result) == 2
                assert isinstance(result[0], str)  # NCT ID
                assert isinstance(result[1], float)  # Score
    
    def test_score_monotonicity(
        self, in_memory_db, mock_medcpt_service,
        mock_bm25_retriever, mock_vector_retriever
    ):
        """Test that returned scores are monotonically decreasing."""
        with Session(in_memory_db) as session:
            retriever = HybridRetriever(
                session,
                mock_medcpt_service,
                mock_bm25_retriever,
                mock_vector_retriever
            )
            
            mock_bm25_retriever.search.return_value = [
                (f"NCT{i:05d}", 10.0 - i) for i in range(10)
            ]
            mock_vector_retriever.search.return_value = [
                (f"NCT{i:05d}", 0.9 - i*0.1) for i in range(10)
            ]
            
            results = retriever.search(["test"], top_n=100)
            
            # Scores should be non-increasing
            scores = [score for _, score in results]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i+1], \
                    f"Scores not monotonic: {scores[i]} < {scores[i+1]}"


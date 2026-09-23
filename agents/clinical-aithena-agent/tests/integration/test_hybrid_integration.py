"""
Integration tests for hybrid retrieval.

These tests require a PostgreSQL database with pgvector extension
and pre-computed embeddings. They test the full hybrid retrieval pipeline.
"""

import os
import pytest
from sqlmodel import Session, create_engine, select

from polus.aithena.clinical_aithena.embeddings import MedCPTService
from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.retrieval import (
    HybridRetriever,
    WeightedHybridRetriever,
)


# Skip all tests in this file if no database URL is provided
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Integration tests require TEST_DATABASE_URL environment variable"
)


@pytest.fixture(scope="module")
def pg_engine():
    """Create PostgreSQL engine for integration testing."""
    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/clinical_aithena_test"
    )
    engine = create_engine(database_url, echo=False)
    return engine


@pytest.fixture(scope="module")
def sample_trials_in_db(pg_engine):
    """Ensure we have trials with embeddings in PostgreSQL."""
    with Session(pg_engine) as session:
        # Check if we have trials with embeddings
        statement = select(TrialGPTStudy).where(
            TrialGPTStudy.text_embedding != None
        ).limit(10)
        
        trials = session.exec(statement).all()
        
        if len(trials) < 3:
            pytest.skip(
                "Need at least 3 trials with embeddings for integration tests. "
                "Run 'ct-aithena embed' first."
            )
        
        return trials


@pytest.fixture
def medcpt_service():
    """Create real MedCPT service for integration testing."""
    try:
        service = MedCPTService()
        # Test that we can generate embeddings
        test_embedding = service.encode_query("test")
        assert len(test_embedding) == 768
        return service
    except Exception as e:
        pytest.skip(f"MedCPT service not available: {e}")


class TestHybridRetrieverIntegration:
    """Integration tests for HybridRetriever with real database."""
    
    def test_search_basic(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test basic hybrid search with real data."""
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            # Search for a common condition
            conditions = ["lung cancer treatment"]
            results = retriever.search(conditions, top_n=20)
            
            # Should return results
            assert len(results) > 0
            assert len(results) <= 20
            
            # Results should be (nct_id, score) tuples
            for nct_id, score in results:
                assert isinstance(nct_id, str)
                assert nct_id.startswith("NCT")
                assert isinstance(score, float)
                assert score > 0.0
            
            # Results should be sorted by score (descending)
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)
    
    def test_search_multi_conditions(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test search with multiple conditions."""
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            # Multiple conditions (simulating TrialGPT keyword generation)
            conditions = [
                "lung cancer stage III",
                "EGFR mutation positive",
                "ECOG performance status"
            ]
            
            results = retriever.search(conditions, top_n=50, rrf_k=20)
            
            # Should return aggregated results
            assert len(results) > 0
            
            # Results should be unique
            nct_ids = [nct_id for nct_id, _ in results]
            assert len(nct_ids) == len(set(nct_ids))
            
            # Scores should be sorted descending
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)
    
    def test_search_performance(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test that hybrid search meets performance requirements."""
        import time
        
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            conditions = ["stage III lung cancer", "EGFR positive"]
            
            # Warm up (build indexes if needed)
            retriever.search(conditions, top_n=100)
            
            # Measure search time
            start_time = time.time()
            results = retriever.search(conditions, top_n=100, rrf_k=20)
            elapsed_time = time.time() - start_time
            
            # Should complete in reasonable time (< 1s for hybrid)
            assert elapsed_time < 1.0, f"Search took {elapsed_time:.3f}s, expected < 1.0s"
            assert len(results) > 0
    
    def test_compare_methods(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test comparing BM25, vector, and hybrid retrieval."""
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            conditions = ["lung cancer treatment"]
            results = retriever.compare_methods(conditions, top_n=50)
            
            # Should have results from all three methods
            assert "bm25" in results
            assert "vector" in results
            assert "hybrid" in results
            
            assert len(results["bm25"]) > 0
            assert len(results["vector"]) > 0
            assert len(results["hybrid"]) > 0
            
            # Hybrid should potentially include results from both
            # (though not guaranteed depending on overlap)
    
    def test_configurable_weights(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test hybrid search with different BM25/vector weights."""
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            conditions = ["lung cancer"]
            
            # Heavy BM25 weight
            results_bm25_heavy = retriever.search(
                conditions,
                top_n=20,
                bm25_weight=2.0,
                vector_weight=0.5
            )
            
            # Heavy vector weight
            results_vector_heavy = retriever.search(
                conditions,
                top_n=20,
                bm25_weight=0.5,
                vector_weight=2.0
            )
            
            # Balanced
            results_balanced = retriever.search(
                conditions,
                top_n=20,
                bm25_weight=1.0,
                vector_weight=1.0
            )
            
            # All should return results
            assert len(results_bm25_heavy) > 0
            assert len(results_vector_heavy) > 0
            assert len(results_balanced) > 0
            
            # Results might differ based on weights
            # (though not guaranteed if overlap is high)
    
    def test_rrf_k_parameter(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test hybrid search with different RRF k values."""
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            conditions = ["lung cancer treatment"]
            
            # Small k (more emphasis on rank)
            results_k10 = retriever.search(conditions, top_n=20, rrf_k=10)
            
            # Default k
            results_k20 = retriever.search(conditions, top_n=20, rrf_k=20)
            
            # Large k (smoother fusion)
            results_k60 = retriever.search(conditions, top_n=20, rrf_k=60)
            
            # All should return results
            assert len(results_k10) > 0
            assert len(results_k20) > 0
            assert len(results_k60) > 0
            
            # Scores should differ with different k values
            # (top result might be same, but scores will differ)
    
    def test_condition_priority_weighting(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test that condition order affects results."""
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            # Same conditions, different order
            conditions_order_1 = ["lung cancer", "stage III", "EGFR mutation"]
            conditions_order_2 = ["EGFR mutation", "stage III", "lung cancer"]
            
            results_1 = retriever.search(conditions_order_1, top_n=50)
            results_2 = retriever.search(conditions_order_2, top_n=50)
            
            # Both should return results
            assert len(results_1) > 0
            assert len(results_2) > 0
            
            # Results might differ due to condition priority weighting
            # (though top results might be similar if highly relevant)
    
    def test_result_quality(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test that hybrid search results are relevant."""
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            # Search for specific condition
            conditions = ["lung cancer"]
            results = retriever.search(conditions, top_n=10)
            
            # Get top result details
            if results:
                top_nct_id = results[0][0]
                trial = session.get(TrialGPTStudy, top_nct_id)
                
                if trial:
                    # Basic relevance check
                    trial_text = f"{trial.title} {trial.text}".lower()
                    assert "lung" in trial_text or "cancer" in trial_text, \
                        f"Top result {top_nct_id} doesn't seem relevant to 'lung cancer'"
    
    def test_get_stats(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test getting hybrid retriever statistics."""
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            stats = retriever.get_stats()
            
            # Should have stats from both retrievers
            assert "bm25_stats" in stats
            assert "vector_stats" in stats
            assert "hybrid_enabled" in stats
            assert stats["hybrid_enabled"] is True


class TestWeightedHybridRetrieverIntegration:
    """Integration tests for WeightedHybridRetriever."""
    
    def test_weighted_vs_standard(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test that weighted and standard RRF produce different results."""
        with Session(pg_engine) as session:
            standard_retriever = HybridRetriever(session, medcpt_service)
            weighted_retriever = WeightedHybridRetriever(session, medcpt_service)
            
            conditions = ["lung cancer treatment"]
            
            results_standard = standard_retriever.search(conditions, top_n=20)
            results_weighted = weighted_retriever.search(conditions, top_n=20)
            
            # Both should return results
            assert len(results_standard) > 0
            assert len(results_weighted) > 0
            
            # Scores should differ
            # (the order might be similar, but scores will be different)
            standard_scores = {nct_id: score for nct_id, score in results_standard}
            weighted_scores = {nct_id: score for nct_id, score in results_weighted}
            
            # Check that at least some scores differ
            # (if there's any overlap in results)
            overlapping_ids = set(standard_scores.keys()) & set(weighted_scores.keys())
            if overlapping_ids:
                some_differ = any(
                    abs(standard_scores[nct_id] - weighted_scores[nct_id]) > 1e-6
                    for nct_id in overlapping_ids
                )
                assert some_differ, "Weighted and standard should produce different scores"


class TestHybridRetrieverPerformance:
    """Performance benchmarks for hybrid retrieval."""
    
    def test_single_condition_performance(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test performance with single condition."""
        import time
        
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            # Warm up
            retriever.search(["test"], top_n=100)
            
            # Measure single condition search
            start_time = time.time()
            results = retriever.search(["lung cancer"], top_n=100)
            elapsed_time = time.time() - start_time
            
            assert elapsed_time < 1.0, f"Single condition search took {elapsed_time:.3f}s"
            assert len(results) > 0
    
    def test_multi_condition_performance(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test performance with multiple conditions."""
        import time
        
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            conditions = [
                "lung cancer",
                "stage III",
                "EGFR mutation",
                "ECOG 0-1",
                "prior chemotherapy"
            ]
            
            # Warm up
            retriever.search(["test"], top_n=100)
            
            # Measure multi-condition search
            start_time = time.time()
            results = retriever.search(conditions, top_n=100)
            elapsed_time = time.time() - start_time
            
            # Should complete in reasonable time even with 5 conditions
            assert elapsed_time < 3.0, \
                f"5-condition search took {elapsed_time:.3f}s, expected < 3.0s"
            assert len(results) > 0
    
    def test_large_top_n_performance(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test performance with large top_n."""
        import time
        
        with Session(pg_engine) as session:
            retriever = HybridRetriever(session, medcpt_service)
            
            # Warm up
            retriever.search(["test"], top_n=100)
            
            # Measure with large top_n
            start_time = time.time()
            results = retriever.search(
                ["lung cancer", "stage III"],
                top_n=1000
            )
            elapsed_time = time.time() - start_time
            
            # Should still be fast due to efficient indexing
            assert elapsed_time < 2.0, \
                f"Large top_n search took {elapsed_time:.3f}s"
            assert len(results) > 0


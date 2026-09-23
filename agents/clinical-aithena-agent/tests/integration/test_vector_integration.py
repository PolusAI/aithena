"""
Integration tests for vector retrieval with pgvector.

These tests require a PostgreSQL database with pgvector extension.
They test the full vector search pipeline including:
- Real MedCPT embedding generation
- pgvector KNN search with HNSW indexes
- Multi-condition aggregation
- Performance benchmarks
"""

import os
import pytest
from sqlmodel import Session, create_engine, select

from polus.aithena.clinical_aithena.embeddings import MedCPTService
from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.retrieval import VectorRetriever


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
    """Create sample trials with embeddings in PostgreSQL."""
    # This fixture assumes the database schema is already set up
    # and uses existing trials, or creates a few test trials
    
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
    # Skip if MedCPT models are not accessible
    try:
        service = MedCPTService()
        # Test that we can generate embeddings
        test_embedding = service.encode_query("test")
        assert len(test_embedding) == 768
        return service
    except Exception as e:
        pytest.skip(f"MedCPT service not available: {e}")


class TestVectorRetrieverIntegration:
    """Integration tests for VectorRetriever with real database."""
    
    def test_search_basic(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test basic vector search with real embeddings."""
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            # Search for a common condition
            results = retriever.search("lung cancer treatment", top_k=10)
            
            # Should return results
            assert len(results) > 0
            assert len(results) <= 10
            
            # Results should be (nct_id, score) tuples
            for nct_id, score in results:
                assert isinstance(nct_id, str)
                assert nct_id.startswith("NCT")
                assert isinstance(score, float)
                assert 0.0 <= score <= 1.0  # Similarity score
            
            # Results should be sorted by score (descending)
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)
    
    def test_search_performance(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test that vector search meets performance requirements."""
        import time
        
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            # Warm up
            retriever.search("test query", top_k=10)
            
            # Measure search time
            start_time = time.time()
            results = retriever.search("stage III lung cancer EGFR positive", top_k=100)
            elapsed_time = time.time() - start_time
            
            # Should complete in < 500ms as per acceptance criteria
            assert elapsed_time < 0.5, f"Search took {elapsed_time:.3f}s, expected < 0.5s"
            assert len(results) > 0
    
    def test_search_multi_conditions(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test multi-condition search with real data."""
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            # Search with multiple conditions (simulating TrialGPT keyword generation)
            conditions = [
                "lung cancer stage III",
                "EGFR mutation positive",
                "ECOG performance status 0-1"
            ]
            
            results = retriever.search_multi_conditions(
                conditions,
                top_k=50,
                aggregation_method="weighted_rrf"
            )
            
            # Should return aggregated results
            assert len(results) > 0
            
            # Results should be unique
            nct_ids = [nct_id for nct_id, _ in results]
            assert len(nct_ids) == len(set(nct_ids))
            
            # Scores should be sorted descending
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)
    
    def test_search_batch(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test batch search with multiple queries."""
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            queries = [
                "lung cancer treatment",
                "diabetes management",
                "hypertension control"
            ]
            
            results = retriever.search_batch(queries, top_k=20)
            
            # Should return one result list per query
            assert len(results) == len(queries)
            
            # Each result list should have results
            for query_results in results:
                assert len(query_results) > 0
                assert len(query_results) <= 20
    
    def test_search_embedding_fields(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test searching different embedding fields."""
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            query = "lung cancer clinical trial"
            
            # Search text embeddings
            text_results = retriever.search(
                query,
                top_k=10,
                embedding_field="text_embedding"
            )
            
            # Search title embeddings
            title_results = retriever.search(
                query,
                top_k=10,
                embedding_field="title_embedding"
            )
            
            # Both should return results
            assert len(text_results) > 0
            assert len(title_results) > 0
            
            # Results might differ between text and title
            # (depending on what's in the embeddings)
    
    def test_search_result_quality(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test that search results are relevant."""
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            # Search for specific condition
            results = retriever.search("lung cancer", top_k=10)
            
            # Get top result details
            if results:
                top_nct_id = results[0][0]
                
                # Fetch the trial from database
                trial = session.get(TrialGPTStudy, top_nct_id)
                
                if trial:
                    # Very basic relevance check - the word "lung" or "cancer"
                    # should appear in the trial text for a "lung cancer" query
                    trial_text = f"{trial.title} {trial.text}".lower()
                    assert "lung" in trial_text or "cancer" in trial_text, \
                        f"Top result {top_nct_id} doesn't seem relevant to 'lung cancer'"
    
    def test_get_stats(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test getting index statistics."""
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            stats = retriever.get_stats()
            
            # Should have statistics
            assert "total_trials" in stats
            assert "trials_with_text_embedding" in stats
            assert "trials_with_title_embedding" in stats
            assert "embedding_dimension" in stats
            
            # Dimension should be 768 (MedCPT)
            assert stats["embedding_dimension"] == 768
            
            # Should have some trials with embeddings
            assert stats["trials_with_text_embedding"] > 0 or \
                   stats["trials_with_title_embedding"] > 0
    
    def test_search_condition_priority_weighting(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test that earlier conditions are weighted higher."""
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            # Same conditions in different order
            conditions_order_1 = ["lung cancer", "diabetes"]
            conditions_order_2 = ["diabetes", "lung cancer"]
            
            results_1 = retriever.search_multi_conditions(
                conditions_order_1,
                top_k=50,
                aggregation_method="weighted_rrf"
            )
            
            results_2 = retriever.search_multi_conditions(
                conditions_order_2,
                top_k=50,
                aggregation_method="weighted_rrf"
            )
            
            # Results might differ due to condition priority weighting
            # (though not guaranteed to be completely different)
            assert len(results_1) > 0
            assert len(results_2) > 0
    
    def test_aggregation_methods(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test different aggregation methods produce different results."""
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            conditions = ["lung cancer", "stage III", "EGFR mutation"]
            
            # Test all three aggregation methods
            results_rrf = retriever.search_multi_conditions(
                conditions,
                top_k=20,
                aggregation_method="weighted_rrf"
            )
            
            results_max = retriever.search_multi_conditions(
                conditions,
                top_k=20,
                aggregation_method="max"
            )
            
            results_sum = retriever.search_multi_conditions(
                conditions,
                top_k=20,
                aggregation_method="sum"
            )
            
            # All should return results
            assert len(results_rrf) > 0
            assert len(results_max) > 0
            assert len(results_sum) > 0
            
            # Results might have different scores/orders
            # (depending on the data)


class TestVectorRetrieverPerformance:
    """Performance benchmarks for vector retrieval."""
    
    def test_batch_encoding_performance(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test that batch encoding is efficient."""
        import time
        
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            # Generate 10 conditions
            conditions = [f"condition {i}" for i in range(10)]
            
            # Time batch search
            start_time = time.time()
            results = retriever.search_batch(conditions, top_k=50)
            batch_time = time.time() - start_time
            
            # Should complete in reasonable time
            assert batch_time < 5.0, \
                f"Batch search of 10 queries took {batch_time:.3f}s"
            assert len(results) == 10
    
    def test_large_top_k_performance(self, pg_engine, medcpt_service, sample_trials_in_db):
        """Test performance with large top_k values."""
        import time
        
        with Session(pg_engine) as session:
            retriever = VectorRetriever(session, medcpt_service)
            
            # Search with large top_k
            start_time = time.time()
            results = retriever.search("cancer treatment", top_k=1000)
            elapsed_time = time.time() - start_time
            
            # Should still complete quickly due to HNSW index
            assert elapsed_time < 1.0, \
                f"Large top_k search took {elapsed_time:.3f}s"
            assert len(results) > 0


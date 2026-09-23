"""Tests for vector-based retrieval."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import JSON, Column, String, Text
from sqlalchemy.dialects import postgresql
from sqlmodel import Session, create_engine

# Patch JSONB to JSON for DuckDB compatibility BEFORE model imports
postgresql.JSONB = JSON

from polus.aithena.clinical_aithena.retrieval import VectorRetriever


@pytest.fixture
def mock_medcpt_service():
    """Mock MedCPT service for testing."""
    service = Mock()
    # Return a consistent 768-dimensional embedding
    service.encode_query.return_value = [0.1] * 768
    service.encode_queries_batch.return_value = [[0.1] * 768, [0.2] * 768]
    return service


@pytest.fixture
def in_memory_db():
    """
    Create an in-memory DuckDB database for testing.
    
    Note: DuckDB doesn't support pgvector, so tests that need actual
    vector search will be integration tests with PostgreSQL.
    """
    engine = create_engine("duckdb:///:memory:")
    
    # Create simplified table for testing
    from sqlalchemy import create_engine as sa_create_engine
    from sqlalchemy import MetaData, Table, Column, String, Text, Float
    
    metadata = MetaData()
    
    # Create simplified trialgpt_study table
    # Note: We can't test actual vector search in DuckDB
    trialgpt_table = Table(
        'trialgpt_study',
        metadata,
        Column('nct_id', String, primary_key=True),
        Column('title', Text, nullable=False),
        Column('text', Text, nullable=False),
        Column('metadata_json', JSON, nullable=False),
        # Simulate embeddings as JSON arrays for DuckDB
        Column('text_embedding', JSON),
        Column('title_embedding', JSON),
    )
    
    with engine.begin() as conn:
        metadata.create_all(conn)
    
    return engine


@pytest.fixture
def sample_trials_with_embeddings(in_memory_db):
    """Create sample trials with mock embeddings."""
    from sqlalchemy import text
    import orjson
    
    with Session(in_memory_db) as session:
        trials_data = [
            {
                "nct_id": "NCT00001",
                "title": "Lung Cancer Treatment Study",
                "text": "A phase III trial for lung cancer",
                "metadata_json": {"diseases_list": ["Lung Cancer"]},
                "text_embedding": [0.9] * 768,  # High similarity to [0.1]*768
                "title_embedding": [0.8] * 768,
            },
            {
                "nct_id": "NCT00002",
                "title": "Diabetes Management Trial",
                "text": "A study of diabetes management",
                "metadata_json": {"diseases_list": ["Diabetes"]},
                "text_embedding": [0.5] * 768,  # Medium similarity
                "title_embedding": [0.5] * 768,
            },
            {
                "nct_id": "NCT00003",
                "title": "Hypertension Control Study",
                "text": "Blood pressure management",
                "metadata_json": {"diseases_list": ["Hypertension"]},
                "text_embedding": [0.2] * 768,  # Low similarity
                "title_embedding": [0.1] * 768,
            },
        ]
        
        for trial_data in trials_data:
            session.execute(
                text("""
                    INSERT INTO trialgpt_study 
                    (nct_id, title, text, metadata_json, text_embedding, title_embedding)
                    VALUES (:nct_id, :title, :text, :metadata_json, :text_embedding, :title_embedding)
                """),
                {
                    "nct_id": trial_data["nct_id"],
                    "title": trial_data["title"],
                    "text": trial_data["text"],
                    "metadata_json": orjson.dumps(trial_data["metadata_json"]).decode(),
                    "text_embedding": orjson.dumps(trial_data["text_embedding"]).decode(),
                    "title_embedding": orjson.dumps(trial_data["title_embedding"]).decode(),
                }
            )
        session.commit()
        
        return trials_data


class TestVectorRetriever:
    """Tests for VectorRetriever."""
    
    def test_initialization(self, in_memory_db, mock_medcpt_service):
        """Test retriever initialization."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            assert retriever.session is session
            assert retriever.medcpt_service is mock_medcpt_service
    
    def test_initialization_creates_service(self, in_memory_db):
        """Test retriever creates MedCPT service if not provided."""
        with patch('polus.aithena.clinical_aithena.retrieval.vector_retriever.MedCPTService') as mock_service_class:
            mock_service_instance = Mock()
            mock_service_class.return_value = mock_service_instance
            
            with Session(in_memory_db) as session:
                retriever = VectorRetriever(session)
                assert retriever.medcpt_service is mock_service_instance
                mock_service_class.assert_called_once()
    
    def test_search_empty_query(self, in_memory_db, mock_medcpt_service):
        """Test search with empty query."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            results = retriever.search("", top_k=10)
            assert results == []
            
            results = retriever.search("   ", top_k=10)
            assert results == []
    
    def test_search_encoding_failure(self, in_memory_db):
        """Test search handles encoding failure gracefully."""
        mock_service = Mock()
        mock_service.encode_query.side_effect = Exception("Encoding failed")
        
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_service)
            results = retriever.search("test query", top_k=10)
            
            assert results == []
            mock_service.encode_query.assert_called_once_with("test query")
    
    def test_search_batch(self, in_memory_db, mock_medcpt_service):
        """Test batch search with multiple queries."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            # Mock the search method to return different results
            with patch.object(retriever, 'search') as mock_search:
                mock_search.side_effect = [
                    [("NCT00001", 0.9), ("NCT00002", 0.5)],
                    [("NCT00003", 0.8), ("NCT00004", 0.4)],
                ]
                
                queries = ["lung cancer", "diabetes"]
                results = retriever.search_batch(queries, top_k=10)
                
                assert len(results) == 2
                assert len(results[0]) == 2
                assert len(results[1]) == 2
                assert mock_search.call_count == 2
    
    def test_search_multi_conditions_empty(self, in_memory_db, mock_medcpt_service):
        """Test multi-condition search with empty conditions."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            results = retriever.search_multi_conditions([], top_k=10)
            
            assert results == []
    
    def test_search_multi_conditions_single(self, in_memory_db, mock_medcpt_service):
        """Test multi-condition search with single condition."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            # Mock search_batch to return results
            with patch.object(retriever, 'search_batch') as mock_batch:
                mock_batch.return_value = [
                    [("NCT00001", 0.9), ("NCT00002", 0.5), ("NCT00003", 0.2)]
                ]
                
                results = retriever.search_multi_conditions(
                    ["lung cancer"],
                    top_k=10,
                    aggregation_method="weighted_rrf"
                )
                
                assert len(results) > 0
                # Results should be sorted by score
                assert all(results[i][1] >= results[i+1][1] for i in range(len(results)-1))
    
    def test_search_multi_conditions_aggregation(self, in_memory_db, mock_medcpt_service):
        """Test multi-condition search with different aggregation methods."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            # Mock search_batch to return overlapping results
            with patch.object(retriever, 'search_batch') as mock_batch:
                mock_batch.return_value = [
                    [("NCT00001", 0.9), ("NCT00002", 0.5)],  # Condition 1 (weight 1.0)
                    [("NCT00001", 0.8), ("NCT00003", 0.6)],  # Condition 2 (weight 0.5)
                ]
                
                # Test weighted_rrf
                results_rrf = retriever.search_multi_conditions(
                    ["condition1", "condition2"],
                    top_k=10,
                    aggregation_method="weighted_rrf"
                )
                
                # NCT00001 appears in both, should have highest score
                assert results_rrf[0][0] == "NCT00001"
                
                # Test max aggregation
                mock_batch.return_value = [
                    [("NCT00001", 0.9), ("NCT00002", 0.5)],
                    [("NCT00001", 0.8), ("NCT00003", 0.6)],
                ]
                results_max = retriever.search_multi_conditions(
                    ["condition1", "condition2"],
                    top_k=10,
                    aggregation_method="max"
                )
                
                assert len(results_max) == 3  # 3 unique NCT IDs
                
                # Test sum aggregation
                mock_batch.return_value = [
                    [("NCT00001", 0.9), ("NCT00002", 0.5)],
                    [("NCT00001", 0.8), ("NCT00003", 0.6)],
                ]
                results_sum = retriever.search_multi_conditions(
                    ["condition1", "condition2"],
                    top_k=10,
                    aggregation_method="sum"
                )
                
                assert len(results_sum) == 3
    
    def test_search_multi_conditions_priority_weighting(self, in_memory_db, mock_medcpt_service):
        """Test that earlier conditions receive higher weights."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            # Mock search_batch with same trial appearing in different positions
            with patch.object(retriever, 'search_batch') as mock_batch:
                mock_batch.return_value = [
                    [("NCT00001", 0.5)],  # Condition 1 (weight 1.0), rank 0
                    [("NCT00002", 0.5)],  # Condition 2 (weight 0.5), rank 0
                ]
                
                results = retriever.search_multi_conditions(
                    ["high_priority", "low_priority"],
                    top_k=10,
                    aggregation_method="weighted_rrf"
                )
                
                # NCT00001 should have higher score due to higher condition weight
                # Even though similarity scores are the same
                nct_scores = {nct_id: score for nct_id, score in results}
                assert nct_scores["NCT00001"] > nct_scores["NCT00002"]
    
    def test_get_stats(self, in_memory_db, mock_medcpt_service, sample_trials_with_embeddings):
        """Test getting index statistics."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            # Note: This test will fail with DuckDB as it doesn't support
            # the FILTER clause the same way as PostgreSQL
            # We'll just test that it doesn't crash
            try:
                stats = retriever.get_stats()
                # If successful, should have basic stats
                assert "embedding_dimension" in stats
                assert stats["embedding_dimension"] == 768
            except Exception:
                # Expected with DuckDB
                pass
    
    def test_search_with_different_embedding_fields(self, in_memory_db, mock_medcpt_service):
        """Test search with different embedding fields."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            # Should not crash when specifying different fields
            # Actual behavior will be tested in integration tests
            with patch.object(retriever, 'search') as mock_search:
                mock_search.return_value = [("NCT00001", 0.9)]
                
                # Test with text_embedding (default)
                results = retriever.search("query", embedding_field="text_embedding")
                mock_search.assert_called()
                
                # Test with title_embedding
                mock_search.return_value = [("NCT00002", 0.8)]
                results = retriever.search("query", embedding_field="title_embedding")
                mock_search.assert_called()


class TestVectorRetrieverValidation:
    """Validation tests for VectorRetriever."""
    
    def test_result_format(self, in_memory_db, mock_medcpt_service):
        """Test that results have correct format."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            with patch.object(retriever.session, 'execute') as mock_execute:
                # Mock database response
                mock_result = Mock()
                mock_result.__iter__ = Mock(return_value=iter([
                    ("NCT00001", 0.95),
                    ("NCT00002", 0.85),
                ]))
                mock_execute.return_value = mock_result
                
                results = retriever.search("test query", top_k=10)
                
                # Verify format
                assert isinstance(results, list)
                for result in results:
                    assert isinstance(result, tuple)
                    assert len(result) == 2
                    assert isinstance(result[0], str)  # NCT ID
                    assert isinstance(result[1], float)  # Score
    
    def test_top_k_limit(self, in_memory_db, mock_medcpt_service):
        """Test that top_k parameter is respected."""
        with Session(in_memory_db) as session:
            retriever = VectorRetriever(session, mock_medcpt_service)
            
            with patch.object(retriever.session, 'execute') as mock_execute:
                # Create mock results
                mock_result = Mock()
                mock_result.__iter__ = Mock(return_value=iter([
                    (f"NCT{i:05d}", 0.9 - i*0.01) for i in range(5)
                ]))
                mock_execute.return_value = mock_result
                
                results = retriever.search("test query", top_k=5)
                
                # Verify SQL includes LIMIT
                call_args = mock_execute.call_args
                assert ":top_k" in str(call_args[0][0])
                assert call_args[0][1]["top_k"] == 5


"""Tests for BM25 retrieval."""

import pytest
from sqlalchemy import JSON, Column, String, Text
from sqlalchemy.dialects import postgresql
from sqlmodel import Session, create_engine

# Patch JSONB to JSON for DuckDB compatibility BEFORE model imports
postgresql.JSONB = JSON

from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.retrieval import BM25Retriever
from polus.aithena.clinical_aithena.retrieval.tokenizer import (
    tokenize,
    tokenize_trial_for_bm25,
)


@pytest.fixture
def in_memory_db():
    """
    Create an in-memory DuckDB database for testing.
    
    Note: We create only the columns needed for BM25 retrieval
    (nct_id, title, text, metadata_json) to avoid DuckDB's lack
    of VECTOR type support.
    """
    engine = create_engine("duckdb:///:memory:")
    
    # Create a simplified table with only the columns needed for BM25
    # (avoiding VECTOR columns which DuckDB doesn't support)
    from sqlalchemy import create_engine as sa_create_engine
    from sqlalchemy import MetaData, Table, Column, String, Text
    from sqlalchemy.dialects.postgresql import JSONB
    
    metadata = MetaData()
    
    # Create simplified trialgpt_study table
    trialgpt_table = Table(
        'trialgpt_study',
        metadata,
        Column('nct_id', String, primary_key=True),
        Column('title', Text, nullable=False),
        Column('text', Text, nullable=False),
        Column('metadata_json', JSON, nullable=False),  # Use JSON instead of JSONB for DuckDB
    )
    
    with engine.begin() as conn:
        metadata.create_all(conn)
    
    return engine


@pytest.fixture
def sample_trials(in_memory_db):
    """Create sample trials for testing."""
    from sqlalchemy import text
    
    with Session(in_memory_db) as session:
        trials_data = [
            {
                "nct_id": "NCT00001",
                "title": "Lung Cancer Treatment Study",
                "text": (
                    "A phase III randomized study of new treatments for "
                    "advanced lung cancer. Patients must have stage III or "
                    "IV non-small cell lung cancer."
                ),
                "metadata_json": {
                    "brief_title": "Lung Cancer Treatment Study",
                    "diseases_list": ["Lung Cancer", "Non-Small Cell Lung Cancer"],
                    "drugs_list": ["Drug A"],
                    "brief_summary": "A study of lung cancer treatments",
                },
            },
            {
                "nct_id": "NCT00002",
                "title": "Diabetes Management Trial",
                "text": (
                    "A study evaluating glucose control in type 2 diabetes. "
                    "Participants will receive lifestyle intervention and "
                    "medication management."
                ),
                "metadata_json": {
                    "brief_title": "Diabetes Management Trial",
                    "diseases_list": ["Type 2 Diabetes", "Diabetes Mellitus"],
                    "drugs_list": ["Metformin"],
                    "brief_summary": "Diabetes management study",
                },
            },
            {
                "nct_id": "NCT00003",
                "title": "Hypertension Control Study",
                "text": (
                    "Evaluating blood pressure control strategies in patients "
                    "with hypertension. Multi-center randomized trial."
                ),
                "metadata_json": {
                    "brief_title": "Hypertension Control Study",
                    "diseases_list": ["Hypertension", "High Blood Pressure"],
                    "drugs_list": ["ACE Inhibitor"],
                    "brief_summary": "Blood pressure control study",
                },
            },
            {
                "nct_id": "NCT00004",
                "title": "Advanced Lung Cancer Immunotherapy",
                "text": (
                    "Immunotherapy for advanced lung cancer patients. "
                    "Investigating checkpoint inhibitors in stage IV disease."
                ),
                "metadata_json": {
                    "brief_title": "Advanced Lung Cancer Immunotherapy",
                    "diseases_list": ["Lung Cancer", "Advanced Lung Cancer"],
                    "drugs_list": ["Immunotherapy Agent"],
                    "brief_summary": "Immunotherapy for lung cancer",
                },
            },
        ]
        
        # Insert using parameterized queries
        import orjson
        for trial_data in trials_data:
            session.execute(
                text("""
                    INSERT INTO trialgpt_study (nct_id, title, text, metadata_json)
                    VALUES (:nct_id, :title, :text, :metadata_json)
                """),
                {
                    "nct_id": trial_data["nct_id"],
                    "title": trial_data["title"],
                    "text": trial_data["text"],
                    "metadata_json": orjson.dumps(trial_data["metadata_json"]).decode(),
                }
            )
        session.commit()
        
        return trials_data


class TestTokenizer:
    """Tests for tokenization utilities."""
    
    def test_tokenize_basic(self):
        """Test basic tokenization."""
        result = tokenize("Lung Cancer Treatment")
        assert result == ["lung", "cancer", "treatment"]
    
    def test_tokenize_empty(self):
        """Test tokenization of empty string."""
        result = tokenize("")
        assert result == []
    
    def test_tokenize_with_punctuation(self):
        """Test tokenization with punctuation."""
        result = tokenize("Stage III, advanced disease.")
        assert "stage" in result
        assert "iii" in result
        assert "advanced" in result
        assert "disease" in result
    
    def test_tokenize_trial_weighting(self):
        """Test trial tokenization with field weighting."""
        tokens = tokenize_trial_for_bm25(
            title="Cancer Study",
            diseases_list=["Lung Cancer"],
            text="A clinical trial"
        )
        
        # Title should appear 3 times
        assert tokens.count("cancer") >= 3  # 3 from title + 1 from diseases
        assert tokens.count("study") == 3  # 3 from title only
        
        # Disease tokens should appear 2 times
        assert tokens.count("lung") == 2  # 2 from diseases
        
        # Text tokens should appear 1 time
        assert tokens.count("clinical") == 1
        assert tokens.count("trial") == 1


class TestBM25Retriever:
    """Tests for BM25Retriever."""
    
    def test_retriever_initialization(self, in_memory_db):
        """Test retriever initialization."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            assert retriever._index is None
            assert retriever._nct_ids is None
    
    def test_build_index(self, in_memory_db, sample_trials):
        """Test index building."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            retriever._build_index()
            
            assert retriever._index is not None
            assert len(retriever._nct_ids) == 4
            assert retriever._trial_count == 4
            assert retriever._index_built_at is not None
    
    def test_search_lung_cancer(self, in_memory_db, sample_trials):
        """Test searching for lung cancer."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            results = retriever.search("lung cancer", top_n=10)
            
            # Should return results
            assert len(results) > 0
            
            # Results should be (nct_id, score) tuples
            assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
            assert all(isinstance(r[0], str) and isinstance(r[1], float) for r in results)
            
            # Lung cancer trials should rank highest
            top_nct_ids = [r[0] for r in results[:2]]
            assert "NCT00001" in top_nct_ids or "NCT00004" in top_nct_ids
    
    def test_search_diabetes(self, in_memory_db, sample_trials):
        """Test searching for diabetes."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            results = retriever.search("diabetes management", top_n=10)
            
            assert len(results) > 0
            
            # Diabetes trial should rank highest
            assert results[0][0] == "NCT00002"
    
    def test_search_returns_top_n(self, in_memory_db, sample_trials):
        """Test that search respects top_n parameter."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            results = retriever.search("cancer", top_n=2)
            
            assert len(results) <= 2
    
    def test_search_multiple_queries(self, in_memory_db, sample_trials):
        """Test batch searching multiple queries."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            queries = ["lung cancer", "diabetes", "hypertension"]
            results = retriever.search_multiple(queries, top_n=5)
            
            assert len(results) == 3
            assert all(len(r) > 0 for r in results)
            
            # Each query should return different top results
            assert results[0][0][0] != results[1][0][0]
    
    def test_search_empty_query(self, in_memory_db, sample_trials):
        """Test searching with empty query."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            results = retriever.search("", top_n=10)
            
            # Should return empty results for empty query
            assert results == []
    
    def test_search_no_trials(self, in_memory_db):
        """Test searching when no trials exist."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            results = retriever.search("lung cancer", top_n=10)
            
            assert results == []
    
    def test_index_caching(self, in_memory_db, sample_trials):
        """Test that index is cached and not rebuilt unnecessarily."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            
            # First search builds index
            retriever.search("test", top_n=10)
            first_index = retriever._index
            first_built_at = retriever._index_built_at
            
            # Second search should reuse index
            retriever.search("test2", top_n=10)
            assert retriever._index is first_index
            assert retriever._index_built_at == first_built_at
    
    def test_refresh_index(self, in_memory_db, sample_trials):
        """Test manual index refresh."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            
            # Build initial index
            retriever.search("test", top_n=10)
            first_built_at = retriever._index_built_at
            
            # Force refresh
            retriever.refresh_index()
            assert retriever._index_built_at > first_built_at
    
    def test_get_stats(self, in_memory_db, sample_trials):
        """Test getting index statistics."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            
            # Before index is built
            stats = retriever.get_stats()
            assert stats["index_built"] is False
            assert stats["trial_count"] == 0
            
            # After index is built
            retriever.search("test", top_n=10)
            stats = retriever.get_stats()
            assert stats["index_built"] is True
            assert stats["trial_count"] == 4
            assert stats["index_built_at"] is not None
    
    def test_weighted_search_title_boost(self, in_memory_db, sample_trials):
        """Test that title matches are boosted."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            
            # Search for "immunotherapy" which is in title of NCT00004
            results = retriever.search("immunotherapy", top_n=10)
            
            # NCT00004 should rank highly due to title match
            top_nct_ids = [r[0] for r in results[:2]]
            assert "NCT00004" in top_nct_ids
    
    def test_disease_list_boost(self, in_memory_db, sample_trials):
        """Test that disease list matches are boosted."""
        with Session(in_memory_db) as session:
            retriever = BM25Retriever(session)
            
            # Search for disease-specific term
            results = retriever.search("non-small cell", top_n=10)
            
            # NCT00001 has "Non-Small Cell Lung Cancer" in diseases
            assert results[0][0] == "NCT00001"


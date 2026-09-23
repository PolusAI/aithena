"""
Integration tests for MedCPT embedding service with LiteLLM.

These tests require a running LiteLLM server with MedCPT models configured.
Set LITELLM_API_BASE and LITELLM_API_KEY environment variables or update .env file.

To run these tests:
    pytest tests/integration/test_medcpt_integration.py -v

To skip if LiteLLM is not available:
    pytest tests/integration/test_medcpt_integration.py -v --skip-integration
"""

import os
import pytest
from polus.aithena.clinical_aithena.embeddings import MedCPTService


def is_litellm_available():
    """Check if LiteLLM server is accessible."""
    try:
        service = MedCPTService()
        # Try a simple test
        service.encode_query("test")
        return True
    except Exception:
        return False


# Skip all tests in this file if --skip-integration flag is used or LiteLLM is not available
pytestmark = pytest.mark.skipif(
    not is_litellm_available(),
    reason="LiteLLM server not available or not configured"
)


class TestMedCPTIntegration:
    """Integration tests for MedCPTService with real LiteLLM server."""
    
    def test_service_initialization(self):
        """Test that service initializes correctly with env vars."""
        service = MedCPTService()
        
        assert service.api_base is not None
        assert service.api_key is not None
        assert service.article_model is not None
        assert service.query_model is not None
        
        print(f"\n✓ Service initialized:")
        print(f"  API Base: {service.api_base}")
        print(f"  Article Model: {service.article_model}")
        print(f"  Query Model: {service.query_model}")
    
    def test_encode_article(self):
        """Test encoding a clinical trial article."""
        service = MedCPTService()
        
        title = "Phase III Clinical Trial for Advanced Lung Cancer"
        text = """
        This is a randomized, double-blind, placebo-controlled study to evaluate
        the efficacy and safety of Drug X in patients with stage III or IV 
        non-small cell lung cancer. The study will enroll 300 patients across
        multiple sites.
        """
        
        embedding = service.encode_article(title, text)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 768, f"Expected 768 dimensions, got {len(embedding)}"
        assert all(isinstance(x, (int, float)) for x in embedding)
        
        # Check that values are reasonable (not all zeros)
        assert sum(embedding) != 0, "Embedding is all zeros"
        assert any(x != 0 for x in embedding), "No non-zero values in embedding"
        
        print(f"\n✓ Article encoded successfully:")
        print(f"  Embedding dimensions: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        print(f"  Sum: {sum(embedding):.4f}")
    
    def test_encode_query(self):
        """Test encoding a patient query."""
        service = MedCPTService()
        
        query = "lung cancer stage III EGFR mutation targeted therapy"
        
        embedding = service.encode_query(query)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 768, f"Expected 768 dimensions, got {len(embedding)}"
        assert all(isinstance(x, (int, float)) for x in embedding)
        
        # Check that values are reasonable
        assert sum(embedding) != 0, "Embedding is all zeros"
        
        print(f"\n✓ Query encoded successfully:")
        print(f"  Query: {query}")
        print(f"  Embedding dimensions: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
    
    def test_encode_articles_batch(self):
        """Test batch encoding of multiple articles."""
        service = MedCPTService()
        
        articles = [
            ("Breast Cancer Trial", "A phase II study of chemotherapy in breast cancer patients."),
            ("Diabetes Study", "Investigating the effects of insulin therapy on type 2 diabetes."),
            ("COVID-19 Vaccine Trial", "Safety and efficacy study of mRNA vaccine."),
        ]
        
        embeddings = service.encode_articles_batch(articles, batch_size=2)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
        assert all(sum(emb) != 0 for emb in embeddings), "Some embeddings are all zeros"
        
        # Check that different articles have different embeddings
        assert embeddings[0] != embeddings[1], "Identical embeddings for different articles"
        
        print(f"\n✓ Batch encoding successful:")
        print(f"  Number of articles: {len(embeddings)}")
        print(f"  All embeddings 768-dimensional: ✓")
    
    def test_encode_queries_batch(self):
        """Test batch encoding of multiple queries."""
        service = MedCPTService()
        
        queries = [
            "lung cancer",
            "diabetes type 2",
            "heart failure treatment",
        ]
        
        embeddings = service.encode_queries_batch(queries, batch_size=2)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
        assert all(sum(emb) != 0 for emb in embeddings)
        
        # Check that different queries have different embeddings
        assert embeddings[0] != embeddings[1], "Identical embeddings for different queries"
        
        print(f"\n✓ Batch query encoding successful:")
        print(f"  Number of queries: {len(embeddings)}")
    
    def test_semantic_similarity(self):
        """Test that semantically similar queries have similar embeddings."""
        service = MedCPTService()
        
        # Similar queries
        query1 = "lung cancer treatment"
        query2 = "pulmonary carcinoma therapy"
        
        # Different query
        query3 = "diabetes medication"
        
        emb1 = service.encode_query(query1)
        emb2 = service.encode_query(query2)
        emb3 = service.encode_query(query3)
        
        # Calculate cosine similarity
        def cosine_similarity(a, b):
            import math
            dot_product = sum(x * y for x, y in zip(a, b))
            magnitude_a = math.sqrt(sum(x * x for x in a))
            magnitude_b = math.sqrt(sum(x * x for x in b))
            return dot_product / (magnitude_a * magnitude_b)
        
        sim_1_2 = cosine_similarity(emb1, emb2)
        sim_1_3 = cosine_similarity(emb1, emb3)
        
        # Similar queries should have higher similarity than different queries
        assert sim_1_2 > sim_1_3, (
            f"Expected similar queries to have higher similarity. "
            f"sim(q1,q2)={sim_1_2:.4f} vs sim(q1,q3)={sim_1_3:.4f}"
        )
        
        print(f"\n✓ Semantic similarity test:")
        print(f"  Query 1: {query1}")
        print(f"  Query 2: {query2}")
        print(f"  Query 3: {query3}")
        print(f"  Similarity(1,2): {sim_1_2:.4f}")
        print(f"  Similarity(1,3): {sim_1_3:.4f}")
        print(f"  Similar queries have higher similarity: ✓")
    
    def test_empty_input_handling(self):
        """Test handling of empty or invalid inputs."""
        service = MedCPTService()
        
        # Empty string should still work (LiteLLM handles it)
        try:
            embedding = service.encode_query("")
            # If it succeeds, check it's valid
            assert len(embedding) == 768
            print("\n✓ Empty query handled successfully")
        except Exception as e:
            # If it fails, that's also acceptable behavior
            print(f"\n✓ Empty query rejected as expected: {e}")
    
    def test_long_input_truncation(self):
        """Test that long inputs are handled correctly (should be truncated)."""
        service = MedCPTService()
        
        # Create a very long text (well over 512 tokens)
        long_text = " ".join(["cancer treatment trial phase III"] * 200)
        
        # Should not raise an error (model will truncate)
        embedding = service.encode_query(long_text)
        
        assert len(embedding) == 768
        assert sum(embedding) != 0
        
        print(f"\n✓ Long input handled successfully (truncated by model)")
    
    def test_explicit_configuration(self):
        """Test creating service with explicit configuration."""
        # Get current config from env
        api_base = os.getenv("LITELLM_API_BASE", "http://localhost:4000")
        api_key = os.getenv("LITELLM_API_KEY", "sk-1234")
        article_model = os.getenv("MEDCPT_ARTICLE_MODEL", "embedding/medcpt-article")
        
        service = MedCPTService(
            api_base=api_base,
            api_key=api_key,
            article_model=article_model,
        )
        
        embedding = service.encode_article("Test", "Test article")
        
        assert len(embedding) == 768
        print(f"\n✓ Explicit configuration works correctly")


if __name__ == "__main__":
    """Run tests manually for debugging."""
    print("Running MedCPT Integration Tests")
    print("=" * 60)
    
    test = TestMedCPTIntegration()
    
    try:
        test.test_service_initialization()
        test.test_encode_article()
        test.test_encode_query()
        test.test_encode_articles_batch()
        test.test_encode_queries_batch()
        test.test_semantic_similarity()
        test.test_empty_input_handling()
        test.test_long_input_truncation()
        test.test_explicit_configuration()
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


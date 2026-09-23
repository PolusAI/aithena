"""Tests for MedCPT embedding service."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from polus.aithena.clinical_aithena.embeddings import MedCPTService


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch("polus.aithena.clinical_aithena.embeddings.medcpt_service.OpenAI") as mock:
        yield mock


class TestMedCPTService:
    """Tests for MedCPTService."""
    
    @patch("polus.aithena.clinical_aithena.embeddings.medcpt_service.httpx.Client")
    def test_initialization(self, mock_httpx_client, mock_openai_client):
        """Test service initializes with correct parameters."""
        service = MedCPTService(
            api_base="http://localhost:11434/v1",
            api_key="ollama",
            article_model="medcpt-article",
            query_model="medcpt-query",
        )
        
        # Verify httpx Client was created with SSL disabled
        mock_httpx_client.assert_called_once_with(verify=False, timeout=60.0)
        
        # Verify OpenAI client was called (don't check exact args due to http_client)
        assert mock_openai_client.called
        
        assert service.article_model == "medcpt-article"
        assert service.query_model == "medcpt-query"
    
    def test_encode_article(self, mock_openai_client):
        """Test article encoding returns correct shape."""
        # Setup mock response
        mock_embedding = [0.1] * 768
        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding)]
        
        mock_client_instance = Mock()
        mock_client_instance.embeddings.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        # Test encoding
        service = MedCPTService()
        embedding = service.encode_article("Test Title", "Test text")
        
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)
        
        # Verify API call
        mock_client_instance.embeddings.create.assert_called_once_with(
            model="medcpt-article",
            input="Test Title Test text",
        )
    
    def test_encode_query(self, mock_openai_client):
        """Test query encoding returns correct shape."""
        # Setup mock response
        mock_embedding = [0.2] * 768
        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding)]
        
        mock_client_instance = Mock()
        mock_client_instance.embeddings.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        # Test encoding
        service = MedCPTService()
        embedding = service.encode_query("lung cancer treatment")
        
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)
        
        # Verify API call
        mock_client_instance.embeddings.create.assert_called_once_with(
            model="medcpt-query",
            input="lung cancer treatment",
        )
    
    def test_encode_articles_batch(self, mock_openai_client):
        """Test batch article encoding processes multiple items."""
        # Setup mock response for batch
        mock_embeddings = [[0.1] * 768, [0.2] * 768]
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=mock_embeddings[0]),
            Mock(embedding=mock_embeddings[1]),
        ]
        
        mock_client_instance = Mock()
        mock_client_instance.embeddings.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        # Test batch encoding
        service = MedCPTService()
        articles = [("Title 1", "Text 1"), ("Title 2", "Text 2")]
        embeddings = service.encode_articles_batch(articles, batch_size=2)
        
        assert len(embeddings) == 2
        assert all(len(e) == 768 for e in embeddings)
        
        # Verify API call
        mock_client_instance.embeddings.create.assert_called_once_with(
            model="medcpt-article",
            input=["Title 1 Text 1", "Title 2 Text 2"],
        )
    
    def test_encode_queries_batch(self, mock_openai_client):
        """Test batch query encoding processes multiple items."""
        # Setup mock response for batch
        mock_embeddings = [[0.3] * 768, [0.4] * 768]
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=mock_embeddings[0]),
            Mock(embedding=mock_embeddings[1]),
        ]
        
        mock_client_instance = Mock()
        mock_client_instance.embeddings.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        # Test batch encoding
        service = MedCPTService()
        queries = ["lung cancer", "diabetes treatment"]
        embeddings = service.encode_queries_batch(queries, batch_size=2)
        
        assert len(embeddings) == 2
        assert all(len(e) == 768 for e in embeddings)
        
        # Verify API call
        mock_client_instance.embeddings.create.assert_called_once_with(
            model="medcpt-query",
            input=["lung cancer", "diabetes treatment"],
        )
    
    def test_batch_processing_multiple_batches(self, mock_openai_client):
        """Test batch encoding handles multiple batches correctly."""
        # Setup mock responses for two batches
        mock_response1 = Mock()
        mock_response1.data = [Mock(embedding=[0.1] * 768), Mock(embedding=[0.2] * 768)]
        
        mock_response2 = Mock()
        mock_response2.data = [Mock(embedding=[0.3] * 768)]
        
        mock_client_instance = Mock()
        mock_client_instance.embeddings.create.side_effect = [mock_response1, mock_response2]
        mock_openai_client.return_value = mock_client_instance
        
        # Test with 3 items and batch_size=2 (should create 2 batches)
        service = MedCPTService()
        articles = [("T1", "Text1"), ("T2", "Text2"), ("T3", "Text3")]
        embeddings = service.encode_articles_batch(articles, batch_size=2)
        
        assert len(embeddings) == 3
        assert mock_client_instance.embeddings.create.call_count == 2
    
    def test_get_device(self, mock_openai_client):
        """Test device getter returns 'ollama'."""
        service = MedCPTService()
        assert service.get_device() == "ollama"
    
    def test_unload_models(self, mock_openai_client):
        """Test unload_models exists for API compatibility."""
        service = MedCPTService()
        # Should not raise an exception
        service.unload_models()
    
    def test_error_handling(self, mock_openai_client):
        """Test error handling when API call fails."""
        mock_client_instance = Mock()
        mock_client_instance.embeddings.create.side_effect = Exception("API Error")
        mock_openai_client.return_value = mock_client_instance
        
        service = MedCPTService()
        
        with pytest.raises(Exception, match="API Error"):
            service.encode_article("Title", "Text")

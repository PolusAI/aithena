"""
MedCPT embedding service for clinical trial and query encoding.

This service uses the ncbi/MedCPT models deployed in Ollama via LiteLLM:
- medcpt-article-encoder: For encoding clinical trial articles
- medcpt-query-encoder: For encoding patient queries

The service uses the OpenAI embeddings API format for compatibility.

Reference: https://github.com/ncbi/MedCPT
"""

import logging
import os
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
import httpx

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class MedCPTService:
    """
    Service for generating MedCPT embeddings for clinical trials and queries using Ollama.
    
    This class uses the OpenAI client to call MedCPT models deployed in Ollama,
    providing a consistent API for embedding generation.
    
    The implementation follows the original TrialGPT approach:
    - Article Encoder: Encodes [title, text] pairs for clinical trials
    - Query Encoder: Encodes patient queries/keywords
    - Output: 768-dimensional embeddings
    
    Example:
        >>> service = MedCPTService(
        ...     api_base="http://localhost:11434/v1",
        ...     article_model="medcpt-article-encoder",
        ...     query_model="medcpt-query-encoder"
        ... )
        >>> # Encode a trial
        >>> embedding = service.encode_article(
        ...     title="Phase III Cancer Trial",
        ...     text="A randomized study of..."
        ... )
        >>> # Encode a query
        >>> query_embedding = service.encode_query("lung cancer treatment")
    """
    
    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        article_model: Optional[str] = None,
        query_model: Optional[str] = None,
    ):
        """
        Initialize the MedCPT service.
        
        Configuration is loaded from environment variables if not provided:
        - LITELLM_API_BASE (or LLM_API_BASE): Base URL for the LiteLLM API
        - LITELLM_API_KEY (or LLM_API_KEY): API key for authentication
        - MEDCPT_ARTICLE_MODEL: Name of the article encoder model
        - MEDCPT_QUERY_MODEL: Name of the query encoder model
        
        Args:
            api_base: Base URL for the LiteLLM API (overrides env vars)
            api_key: API key for authentication (overrides env vars)
            article_model: Name of the article encoder model (overrides MEDCPT_ARTICLE_MODEL)
            query_model: Name of the query encoder model (overrides MEDCPT_QUERY_MODEL)
        """
        # Load from environment variables with fallback chain:
        # LITELLM_* (legacy) -> LLM_* (standard) -> hardcoded default
        self.api_base = (
            api_base
            or os.getenv("LITELLM_API_BASE")
            or os.getenv("LLM_API_BASE", "http://localhost:4000")
        )
        self.api_key = (
            api_key
            or os.getenv("LITELLM_API_KEY")
            or os.getenv("LLM_API_KEY", "sk-1234")
        )
        self.article_model = article_model or os.getenv("MEDCPT_ARTICLE_MODEL", "medcpt-article")
        self.query_model = query_model or os.getenv("MEDCPT_QUERY_MODEL", "medcpt-query")
        
        # Create httpx client with SSL verification disabled for self-signed certificates
        http_client = httpx.Client(verify=False, timeout=60.0)
        
        # Use OpenAI client with custom base URL (LiteLLM proxy is OpenAI-compatible)
        self.client = OpenAI(
            base_url=self.api_base,
            api_key=self.api_key,
            http_client=http_client,
        )
        
        logger.info(f"Initialized MedCPT service with LiteLLM proxy at {self.api_base}")
        logger.info(f"  Article model: {self.article_model}")
        logger.info(f"  Query model: {self.query_model}")
    
    def encode_article(
        self,
        title: str,
        text: str,
    ) -> List[float]:
        """
        Encode a clinical trial article (title + text) into an embedding.
        
        This follows the TrialGPT approach of encoding [title, text] pairs
        using the MedCPT Article Encoder.
        
        Args:
            title: Trial title
            text: Trial text (typically summary + criteria)
            
        Returns:
            768-dimensional embedding vector
            
        Example:
            >>> embedding = service.encode_article(
            ...     "Cancer Treatment Study",
            ...     "A phase III trial investigating..."
            ... )
            >>> len(embedding)
            768
        """
        # Combine title and text with separator (as in original MedCPT)
        input_text = f"{title} {text}"
        
        try:
            response = self.client.embeddings.create(
                model=self.article_model,
                input=input_text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to encode article: {e}")
            raise
    
    def encode_articles_batch(
        self,
        articles: List[Tuple[str, str]],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """
        Encode multiple articles in batches for efficiency.
        
        Args:
            articles: List of (title, text) tuples
            batch_size: Number of articles to process at once
            
        Returns:
            List of 768-dimensional embedding vectors
            
        Example:
            >>> articles = [
            ...     ("Trial 1", "Description 1"),
            ...     ("Trial 2", "Description 2"),
            ... ]
            >>> embeddings = service.encode_articles_batch(articles)
            >>> len(embeddings)
            2
        """
        all_embeddings = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            # Prepare batch input
            input_texts = [f"{title} {text}" for title, text in batch]
            
            try:
                response = self.client.embeddings.create(
                    model=self.article_model,
                    input=input_texts,
                )
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to encode batch starting at index {i}: {e}")
                raise
        
        return all_embeddings
    
    def encode_query(self, query: str) -> List[float]:
        """
        Encode a patient query/keywords into an embedding.
        
        This uses the MedCPT Query Encoder for encoding patient queries,
        which is optimized for cross-encoder retrieval with the Article Encoder.
        
        Args:
            query: Patient query text (e.g., keywords, clinical note summary)
            
        Returns:
            768-dimensional embedding vector
            
        Example:
            >>> embedding = service.encode_query("lung cancer stage III")
            >>> len(embedding)
            768
        """
        try:
            response = self.client.embeddings.create(
                model=self.query_model,
                input=query,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to encode query: {e}")
            raise
    
    def encode_queries_batch(
        self,
        queries: List[str],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """
        Encode multiple queries in batches for efficiency.
        
        Args:
            queries: List of query strings
            batch_size: Number of queries to process at once
            
        Returns:
            List of 768-dimensional embedding vectors
            
        Example:
            >>> queries = ["lung cancer", "diabetes treatment"]
            >>> embeddings = service.encode_queries_batch(queries)
            >>> len(embeddings)
            2
        """
        all_embeddings = []
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.query_model,
                    input=batch,
                )
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to encode query batch starting at index {i}: {e}")
                raise
        
        return all_embeddings
    
    def get_device(self) -> str:
        """
        Get the device being used.
        
        Note: With Ollama, the device is managed by the Ollama server.
        This method exists for API compatibility.
        """
        return "ollama"
    
    def unload_models(self):
        """
        Unload models from memory.
        
        Note: With Ollama, model lifecycle is managed by the Ollama server.
        This method exists for API compatibility but is a no-op.
        """
        logger.info("Model lifecycle managed by Ollama server")

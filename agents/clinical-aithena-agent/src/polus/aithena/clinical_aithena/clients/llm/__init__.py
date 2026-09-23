"""Simple LLM client utilities using OpenAI SDK + LiteLLM."""

from typing import Optional

from openai import OpenAI

from polus.aithena.clinical_aithena.clients.llm.config import LLMConfig
from polus.aithena.clinical_aithena.clients.llm.utils import parse_json_response


def get_client(config: Optional[LLMConfig] = None) -> OpenAI:
    """
    Get an OpenAI client configured for LiteLLM.
    
    LiteLLM provides an OpenAI-compatible interface for all major LLM providers
    (OpenAI, Azure, Anthropic, Cohere, etc.) with built-in retries, fallbacks,
    and rate limiting.
    
    Args:
        config: LLM configuration. If None, loads from environment variables.
        
    Returns:
        Configured OpenAI client instance
        
    Raises:
        ValueError: If configuration is invalid
        
    Example:
        >>> from polus.aithena.clinical_aithena.clients.llm import (
        ...     get_client,
        ...     parse_json_response
        ... )
        
        >>> # Get client (uses environment variables)
        >>> client = get_client()
        
        >>> # Make a chat completion
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     temperature=0
        ... )
        >>> print(response.choices[0].message.content)
        
        >>> # Parse JSON response
        >>> json_response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Return JSON"}],
        ...     temperature=0
        ... )
        >>> data = parse_json_response(json_response.choices[0].message.content)
    """
    if config is None:
        config = LLMConfig()
    
    if not config.is_configured:
        raise ValueError(
            "LLM client is not properly configured. "
            "Set LLM_API_KEY and LLM_API_BASE environment variables."
        )
    
    return OpenAI(
        api_key=config.api_key,
        base_url=config.api_base,
        timeout=config.timeout,
    )


__all__ = ["LLMConfig", "get_client", "parse_json_response"]

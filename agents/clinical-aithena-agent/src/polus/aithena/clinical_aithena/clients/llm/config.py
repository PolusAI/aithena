"""Configuration for LLM clients."""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """
    Configuration for LLM clients using OpenAI-compatible API.
    
    Works with any LiteLLM-compatible endpoint (OpenAI, Azure, Anthropic, etc.)
    by configuring the appropriate base URL and API key.
    
    Environment Variables:
        LLM_MODEL: Model name (e.g., "gpt-4", "claude-3-opus")
        LLM_API_KEY or OPENAI_API_KEY: API key for authentication
        LLM_API_BASE or OPENAI_ENDPOINT: API endpoint URL
        LLM_TEMPERATURE: Temperature for generation (0.0-2.0)
        LLM_MAX_RETRIES: Maximum retry attempts (default 3)
        LLM_TIMEOUT: Request timeout in seconds (default 60)
    """
    
    model: str = Field(
        default="gpt-4",
        description="Model name (e.g., 'gpt-4', 'claude-3-opus-20240229')",
    )
    
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication",
    )
    
    api_base: Optional[str] = Field(
        default="https://api.openai.com/v1",
        description="API endpoint URL (use LiteLLM proxy URL for multi-provider)",
    )
    
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for generation",
    )
    
    max_retries: int = Field(
        default=3,
        ge=1,
        description="Maximum number of retry attempts",
    )
    
    timeout: int = Field(
        default=60,
        ge=1,
        description="Request timeout in seconds",
    )

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars from .env file
    )

    def __init__(self, **kwargs):
        """
        Initialize LLM configuration.
        
        Handles fallback environment variables for backward compatibility:
        - OPENAI_API_KEY → LLM_API_KEY
        - OPENAI_ENDPOINT → LLM_API_BASE
        """
        super().__init__(**kwargs)
        
        # Fallback to OPENAI_* env vars if LLM_* not set
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_base or self.api_base == "https://api.openai.com/v1":
            # Check for OPENAI_ENDPOINT (Azure-style env var)
            endpoint = os.getenv("OPENAI_ENDPOINT")
            if endpoint:
                self.api_base = endpoint

    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self.api_key and self.api_base)


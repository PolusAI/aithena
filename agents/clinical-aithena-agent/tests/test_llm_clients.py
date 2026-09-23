"""Tests for LLM client utilities."""

import pytest

from polus.aithena.clinical_aithena.clients.llm import (
    LLMConfig,
    get_client,
    parse_json_response,
)


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LLMConfig()
        assert config.model == "gpt-4"
        assert config.api_base == "https://api.openai.com/v1"
        assert config.temperature == 0.0
        assert config.max_retries == 3
        assert config.timeout == 60

    def test_config_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("LLM_MODEL", "gpt-4-turbo")
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_API_BASE", "https://litellm.example.com")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.5")
        
        config = LLMConfig()
        assert config.model == "gpt-4-turbo"
        assert config.api_key == "test-key"
        assert config.api_base == "https://litellm.example.com"
        assert config.temperature == 0.5

    def test_fallback_to_openai_env_vars(self, monkeypatch):
        """Test fallback to OPENAI_* environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "fallback-key")
        monkeypatch.setenv("OPENAI_ENDPOINT", "https://fallback.endpoint")
        
        config = LLMConfig()
        assert config.api_key == "fallback-key"
        assert config.api_base == "https://fallback.endpoint"

    def test_is_configured(self):
        """Test is_configured property."""
        config = LLMConfig(
            api_key="test-key",
            api_base="https://test.endpoint"
        )
        assert config.is_configured is True
        
        config = LLMConfig()  # Missing api_key
        assert config.is_configured is False


class TestJSONParsing:
    """Tests for JSON response parsing."""

    def test_parse_json_with_markdown_fences(self):
        """Test parsing JSON with markdown code fences."""
        response = '```json\n{"summary": "Test", "conditions": ["A", "B"]}\n```'
        result = parse_json_response(response)
        assert result == {"summary": "Test", "conditions": ["A", "B"]}

    def test_parse_json_with_triple_backticks(self):
        """Test parsing JSON with plain triple backticks."""
        response = '```\n{"summary": "Test"}\n```'
        result = parse_json_response(response)
        assert result == {"summary": "Test"}

    def test_parse_json_with_inline_backticks(self):
        """Test parsing JSON with inline backticks."""
        response = '```{"summary": "Test"}```'
        result = parse_json_response(response)
        assert result == {"summary": "Test"}

    def test_parse_plain_json(self):
        """Test parsing plain JSON without markdown."""
        response = '{"summary": "Test", "value": 123}'
        result = parse_json_response(response)
        assert result == {"summary": "Test", "value": 123}

    def test_parse_json_with_json_label(self):
        """Test parsing JSON that starts with 'json' label."""
        response = 'json\n{"test": "value"}'
        result = parse_json_response(response)
        assert result == {"test": "value"}

    def test_parse_invalid_json_raises_error(self):
        """Test that invalid JSON raises appropriate error."""
        with pytest.raises(Exception):  # JSONDecodeError
            parse_json_response("not valid json")


class TestGetClient:
    """Tests for get_client function."""

    def test_get_client_with_valid_config(self, monkeypatch):
        """Test creating client with valid configuration."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_API_BASE", "https://test.endpoint")
        
        client = get_client()
        
        assert client is not None
        assert client.base_url == "https://test.endpoint"

    def test_get_client_with_explicit_config(self):
        """Test creating client with explicit config."""
        config = LLMConfig(
            api_key="test-key",
            api_base="https://api.openai.com/v1"
        )
        
        client = get_client(config)
        
        assert client is not None
        # OpenAI client adds trailing slash
        assert str(client.base_url).rstrip("/") == "https://api.openai.com/v1"

    def test_get_client_raises_on_invalid_config(self):
        """Test that get_client raises error with invalid config."""
        config = LLMConfig()  # Missing required fields
        
        with pytest.raises(ValueError, match="not properly configured"):
            get_client(config)

"""Tests for API configuration."""

import os

import pytest

from polus.aithena.clinical_aithena.api.core.config import Settings


def test_default_settings():
    """Test that default settings are loaded correctly."""
    settings = Settings()

    assert settings.api_title == "Clinical Aithena API"
    assert settings.api_version == "0.1.0"
    assert settings.api_description == "API for querying clinical trials data"
    assert settings.cors_origins == ["*"]
    assert "postgresql" in settings.database_url


def test_cors_origins_from_string():
    """Test that CORS origins can be parsed from a comma-separated string."""
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,https://example.com"
    settings = Settings()

    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://example.com",
    ]

    # Clean up
    del os.environ["CORS_ORIGINS"]


def test_cors_origins_with_spaces():
    """Test that CORS origins strips whitespace correctly."""
    os.environ["CORS_ORIGINS"] = "http://localhost:3000 , https://example.com"
    settings = Settings()

    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://example.com",
    ]

    # Clean up
    del os.environ["CORS_ORIGINS"]


def test_custom_api_settings():
    """Test that custom API settings can be set via environment variables."""
    os.environ["API_TITLE"] = "Test API"
    os.environ["API_VERSION"] = "1.0.0"
    os.environ["API_DESCRIPTION"] = "Test Description"

    settings = Settings()

    assert settings.api_title == "Test API"
    assert settings.api_version == "1.0.0"
    assert settings.api_description == "Test Description"

    # Clean up
    del os.environ["API_TITLE"]
    del os.environ["API_VERSION"]
    del os.environ["API_DESCRIPTION"]


def test_database_url_override():
    """Test that database URL can be overridden via environment variable."""
    custom_url = "postgresql+psycopg://testuser:testpass@testhost:5432/testdb"
    os.environ["DATABASE_URL"] = custom_url

    settings = Settings()

    assert settings.database_url == custom_url

    # Clean up
    del os.environ["DATABASE_URL"]


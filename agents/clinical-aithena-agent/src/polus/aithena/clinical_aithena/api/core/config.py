"""Configuration settings for the Clinical Aithena API."""

from __future__ import annotations

from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    database_url: str = (
        "postgresql+psycopg://postgres:CHANGE_ME_POSTGRES_PASSWORD@localhost:5432/"
        "clinical_aithena"
    )

    # API Configuration
    api_title: str = "Clinical Aithena API"
    api_version: str = "0.1.0"
    api_description: str = "API for querying clinical trials data"
    api_root_path: str = ""  # Set to "/apis/ctaithena" when behind reverse proxy

    # RabbitMQ Configuration (for GARDIAN real-time status updates)
    rabbitmq_url: str = "amqp://guest:guest@localhost/"

    # CORS Configuration
    # Can be a comma-separated string or a list
    cors_origins: Union[List[str], str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()

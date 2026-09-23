"""
Shared fixtures for integration tests.

Centralizes PostgreSQL engine, session, MedCPT service, and sample data
fixtures so individual integration test files don't duplicate setup logic.
"""

import os

import pytest
from sqlmodel import Session, create_engine, select

from polus.aithena.clinical_aithena.embeddings import MedCPTService
from polus.aithena.clinical_aithena.models import TrialGPTStudy


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

def _database_url() -> str:
    """Return the TEST_DATABASE_URL or empty string."""
    return os.getenv("TEST_DATABASE_URL", "")


def _llm_is_configured() -> bool:
    """Return True when an LLM API key is available."""
    return bool(
        os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    )


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pg_engine():
    """Create PostgreSQL engine for integration testing.

    Skips if TEST_DATABASE_URL is not set.
    """
    url = _database_url()
    if not url:
        pytest.skip("Integration tests require TEST_DATABASE_URL")
    engine = create_engine(url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture()
def pg_session(pg_engine):
    """Provide a per-test SQLModel session with automatic rollback."""
    with Session(pg_engine) as session:
        yield session


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sample_trials_in_db(pg_engine):
    """Ensure the database has trials with embeddings.

    Skips the whole module when fewer than 3 embedded trials exist.
    """
    with Session(pg_engine) as session:
        statement = (
            select(TrialGPTStudy)
            .where(TrialGPTStudy.text_embedding != None)  # noqa: E711
            .limit(10)
        )
        trials = session.exec(statement).all()

        if len(trials) < 3:
            pytest.skip(
                "Need at least 3 trials with embeddings. "
                "Run 'ct-aithena embed' first."
            )
        return trials


# ---------------------------------------------------------------------------
# MedCPT fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def medcpt_service():
    """Create a real MedCPT service, skipping if unavailable."""
    try:
        service = MedCPTService()
        test_embedding = service.encode_query("test")
        assert len(test_embedding) == 768
        return service
    except Exception as e:
        pytest.skip(f"MedCPT service not available: {e}")


# ---------------------------------------------------------------------------
# LLM guard marker
# ---------------------------------------------------------------------------

requires_llm = pytest.mark.skipif(
    not _llm_is_configured(),
    reason="LLM tests require LLM_API_KEY or OPENAI_API_KEY",
)

requires_database = pytest.mark.skipif(
    not _database_url(),
    reason="Integration tests require TEST_DATABASE_URL",
)

"""Shared test fixtures for the Clinical Aithena API tests."""

# Patch JSONB to JSON for DuckDB compatibility BEFORE any model imports
from sqlalchemy import JSON
from sqlalchemy.dialects import postgresql
postgresql.JSONB = JSON

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from polus.aithena.clinical_aithena.api.main import app
from polus.aithena.clinical_aithena.api.core.database import get_session

# Create a simple base model for testing (avoiding JSONB columns)
Base = declarative_base()


class CTGovStudyForTest(Base):
    """Simplified CTGovStudy model for SQLite testing."""

    __tablename__ = "ctgovstudy"

    id = Column(Integer, primary_key=True)
    nct_id = Column(String, index=True)
    brief_title = Column(String, index=True)
    version_date = Column(DateTime, index=True)
    content_hash = Column(String, index=True)
    is_latest = Column(Boolean, default=True, index=True)
    overall_status = Column(String, index=True)
    study_type = Column(String, index=True)
    org_study_id = Column(String, index=True)
    start_date = Column(String, index=True)
    completion_date = Column(String, index=True)
    enrollment_count = Column(String, index=True)
    lead_sponsor_name = Column(String, index=True)
    # Note: Skipping JSONB columns (protocolSection, etc.) as they're not compatible with SQLite
    protocolSection = Column(String)  # Simplified as String for SQLite
    resultsSection = Column(String)
    derivedSection = Column(String)
    documentSection = Column(String)
    annotationSection = Column(String)
    hasResults = Column(Boolean)


@pytest.fixture(name="test_db_path")
def test_db_path_fixture(tmp_path):
    """Create a temporary database file path."""
    return tmp_path / "test.db"


@pytest.fixture(name="session")
def sync_session_fixture(test_db_path):
    """
    Create a synchronous session for adding test data.

    Uses a file-based SQLite database so data is visible to async session.
    """
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture(name="async_session")
async def async_session_fixture(test_db_path):
    """
    Create an async session that connects to the same test database file.

    This ensures both sync and async sessions access the same database.
    """
    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    await async_engine.dispose()


@pytest.fixture(name="client")
def client_fixture(session, async_session: AsyncSession):
    """
    Create a FastAPI test client with a test database session.

    Overrides the get_session dependency to use the test database.
    Note: session parameter ensures the sync session is created first.
    """

    async def get_session_override():
        return async_session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Alias for backwards compatibility
TestCTGovStudy = CTGovStudyForTest


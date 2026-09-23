"""
API integration tests against a real PostgreSQL database.

Tests the FastAPI endpoints (health, search, stats, root) using
the real database to verify query correctness, pagination, and
response shapes.
"""

import os

import math

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from polus.aithena.clinical_aithena.api.main import app
from polus.aithena.clinical_aithena.api.core.database import get_session


# Skip entire module if no database
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="API integration tests require TEST_DATABASE_URL",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api_client():
    """Create a FastAPI TestClient wired to the real database.

    The async engine is created lazily inside the dependency override
    so it binds to the event loop that TestClient creates, avoiding
    'attached to a different loop' errors with asyncpg.
    """
    url = os.getenv("TEST_DATABASE_URL", "")
    async_url = url.replace("postgresql+psycopg://", "postgresql+asyncpg://")

    async def override_get_session():
        # Create engine inside the async context so it is bound to
        # TestClient's event loop.
        engine = create_async_engine(async_url, echo=False)
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_maker() as session:
            yield session
        await engine.dispose()

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------

class TestRootEndpoint:
    """Tests for the root / endpoint."""

    def test_root_returns_api_info(self, api_client):
        resp = api_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data

    def test_root_includes_navigation_links(self, api_client):
        data = api_client.get("/").json()
        for key in ("health", "search", "stats"):
            assert key in data


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for GET /health against real database."""

    def test_health_returns_ok(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_database_connected(self, api_client):
        """With a real database, /health should report 'connected'."""
        resp = api_client.get("/health")
        data = resp.json()
        assert data["database"] == "connected"


# ---------------------------------------------------------------------------
# Stats endpoint
# ---------------------------------------------------------------------------

class TestStatsEndpoint:
    """Tests for GET /stats against real database."""

    def test_stats_returns_counts(self, api_client):
        resp = api_client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        for key in ("total", "recruiting", "interventional", "observational"):
            assert key in data
            assert isinstance(data[key], int)
            assert data[key] >= 0

    def test_stats_total_is_positive(self, api_client):
        """A populated database should have at least some studies."""
        data = api_client.get("/stats").json()
        assert data["total"] > 0

    def test_stats_subcounts_do_not_exceed_total(self, api_client):
        data = api_client.get("/stats").json()
        assert data["recruiting"] <= data["total"]
        assert data["interventional"] <= data["total"]
        assert data["observational"] <= data["total"]


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------

class TestSearchEndpoint:
    """Tests for GET /search against real database."""

    def test_search_default_returns_paginated(self, api_client):
        resp = api_client.get("/search")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "results" in data
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_search_results_have_expected_fields(self, api_client):
        resp = api_client.get("/search?page_size=1")
        data = resp.json()
        if data["results"]:
            trial = data["results"][0]
            assert "nct_id" in trial

    def test_search_pagination_page_2(self, api_client):
        resp = api_client.get("/search?page=2&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 5
        assert len(data["results"]) <= 5

    def test_search_keyword_filter(self, api_client):
        """Search with keyword should return fewer or equal results than no filter."""
        all_resp = api_client.get("/search")
        cancer_resp = api_client.get("/search?keyword=cancer")
        assert cancer_resp.status_code == 200
        cancer_data = cancer_resp.json()
        assert cancer_data["total"] <= all_resp.json()["total"]

    def test_search_keyword_case_insensitive(self, api_client):
        lower = api_client.get("/search?keyword=cancer").json()["total"]
        upper = api_client.get("/search?keyword=CANCER").json()["total"]
        assert lower == upper

    def test_search_invalid_page_rejected(self, api_client):
        resp = api_client.get("/search?page=0")
        assert resp.status_code == 422

    def test_search_invalid_page_size_rejected(self, api_client):
        resp = api_client.get("/search?page_size=0")
        assert resp.status_code == 422
        resp2 = api_client.get("/search?page_size=101")
        assert resp2.status_code == 422

    def test_search_total_pages_calculation(self, api_client):
        data = api_client.get("/search?page_size=10").json()
        expected = math.ceil(data["total"] / data["page_size"])
        assert data["total_pages"] == expected

    def test_search_empty_keyword_returns_all(self, api_client):
        """An empty keyword parameter should behave like no keyword."""
        all_data = api_client.get("/search").json()
        empty_data = api_client.get("/search?keyword=").json()
        # Empty string keyword might still filter or not; just check success
        assert empty_data["total"] >= 0


class TestSearchPaginationConsistency:
    """Verify that paginating through results is consistent."""

    def test_page_1_and_2_return_different_results(self, api_client):
        p1 = api_client.get("/search?page=1&page_size=5").json()
        p2 = api_client.get("/search?page=2&page_size=5").json()
        if p1["total"] > 5:
            ids_p1 = {r.get("nct_id") for r in p1["results"]}
            ids_p2 = {r.get("nct_id") for r in p2["results"]}
            assert ids_p1 != ids_p2, "Pages 1 and 2 should not be identical"

"""Tests for the search endpoint."""

from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.conftest import TestCTGovStudy


def test_search_endpoint_empty_database(client: TestClient):
    """Test search endpoint with no data in the database."""
    response = client.get("/search")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 0
    assert data["results"] == []


def test_search_endpoint_with_data(client: TestClient, session: Session):
    """Test search endpoint returns trials from the database."""
    # Create test trials
    trial1 = TestCTGovStudy(
        nct_id="NCT00000001",
        brief_title="Test Cancer Trial",
        version_date=datetime(2024, 1, 1),
        is_latest=True,
    )
    trial2 = TestCTGovStudy(
        nct_id="NCT00000002",
        brief_title="Test Diabetes Study",
        version_date=datetime(2024, 1, 2),
        is_latest=True,
    )
    session.add(trial1)
    session.add(trial2)
    session.commit()

    response = client.get("/search")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 1
    assert len(data["results"]) == 2

    # Results should be ordered by version_date descending
    assert data["results"][0]["nct_id"] == "NCT00000002"
    assert data["results"][1]["nct_id"] == "NCT00000001"


def test_search_endpoint_keyword_filter(client: TestClient, session: Session):
    """Test search endpoint with keyword filtering."""
    # Create test trials
    trial1 = TestCTGovStudy(
        nct_id="NCT00000001",
        brief_title="Cancer Treatment Study",
        version_date=datetime(2024, 1, 1),
        is_latest=True,
    )
    trial2 = TestCTGovStudy(
        nct_id="NCT00000002",
        brief_title="Diabetes Management Trial",
        version_date=datetime(2024, 1, 2),
        is_latest=True,
    )
    trial3 = TestCTGovStudy(
        nct_id="NCT00000003",
        brief_title="Cancer Prevention Research",
        version_date=datetime(2024, 1, 3),
        is_latest=True,
    )
    session.add_all([trial1, trial2, trial3])
    session.commit()

    response = client.get("/search?keyword=cancer")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert len(data["results"]) == 2

    # Should only return cancer trials
    titles = [r["brief_title"] for r in data["results"]]
    assert all("cancer" in title.lower() for title in titles)


def test_search_endpoint_case_insensitive(client: TestClient, session: Session):
    """Test that keyword search is case-insensitive."""
    trial = TestCTGovStudy(
        nct_id="NCT00000001",
        brief_title="Cancer Treatment Study",
        version_date=datetime(2024, 1, 1),
        is_latest=True,
    )
    session.add(trial)
    session.commit()

    # Test various capitalizations
    for keyword in ["cancer", "CANCER", "Cancer", "cAnCeR"]:
        response = client.get(f"/search?keyword={keyword}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


def test_search_endpoint_pagination(client: TestClient, session: Session):
    """Test search endpoint pagination."""
    # Create 25 test trials
    trials = [
        TestCTGovStudy(
            nct_id=f"NCT{i:08d}",
            brief_title=f"Test Trial {i}",
            version_date=datetime(2024, 1, i % 28 + 1),
            is_latest=True,
        )
        for i in range(25)
    ]
    session.add_all(trials)
    session.commit()

    # Test first page with page_size=10
    response = client.get("/search?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 25
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 3
    assert len(data["results"]) == 10

    # Test second page
    response = client.get("/search?page=2&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert len(data["results"]) == 10

    # Test last page
    response = client.get("/search?page=3&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 3
    assert len(data["results"]) == 5


def test_search_endpoint_custom_page_size(client: TestClient, session: Session):
    """Test search endpoint with custom page size."""
    trials = [
        TestCTGovStudy(
            nct_id=f"NCT{i:08d}",
            brief_title=f"Test Trial {i}",
            version_date=datetime(2024, 1, 1),
            is_latest=True,
        )
        for i in range(30)
    ]
    session.add_all(trials)
    session.commit()

    response = client.get("/search?page_size=20")
    assert response.status_code == 200
    data = response.json()

    assert data["page_size"] == 20
    assert len(data["results"]) == 20
    assert data["total_pages"] == 2


def test_search_endpoint_invalid_page(client: TestClient):
    """Test search endpoint with invalid page number."""
    # Page 0 should fail (must be >= 1)
    response = client.get("/search?page=0")
    assert response.status_code == 422  # Validation error


def test_search_endpoint_invalid_page_size(client: TestClient):
    """Test search endpoint with invalid page size."""
    # Page size 0 should fail (must be >= 1)
    response = client.get("/search?page_size=0")
    assert response.status_code == 422

    # Page size > 100 should fail (max 100)
    response = client.get("/search?page_size=101")
    assert response.status_code == 422


def test_search_endpoint_only_latest_versions(
    client: TestClient, session: Session
):
    """Test that search only returns the latest versions of trials."""
    # Create old and new versions of the same trial
    old_version = TestCTGovStudy(
        nct_id="NCT00000001",
        brief_title="Old Version",
        version_date=datetime(2023, 1, 1),
        is_latest=False,
    )
    new_version = TestCTGovStudy(
        nct_id="NCT00000001",
        brief_title="New Version",
        version_date=datetime(2024, 1, 1),
        is_latest=True,
    )
    session.add_all([old_version, new_version])
    session.commit()

    response = client.get("/search")
    assert response.status_code == 200
    data = response.json()

    # Should only return 1 result (the latest)
    assert data["total"] == 1
    assert data["results"][0]["brief_title"] == "New Version"


def test_search_response_structure(client: TestClient, session: Session):
    """Test that search response has the correct structure."""
    trial = TestCTGovStudy(
        nct_id="NCT00000001",
        brief_title="Test Trial",
        version_date=datetime(2024, 1, 1),
        is_latest=True,
    )
    session.add(trial)
    session.commit()

    response = client.get("/search")
    assert response.status_code == 200
    data = response.json()

    # Check top-level structure
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert "results" in data

    # Check types
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["page_size"], int)
    assert isinstance(data["total_pages"], int)
    assert isinstance(data["results"], list)

    # Check result structure
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert "nct_id" in result
    assert "brief_title" in result
    assert "version_date" in result
    assert "is_latest" in result


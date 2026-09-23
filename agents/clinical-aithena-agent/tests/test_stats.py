"""Tests for the stats endpoint."""

from fastapi.testclient import TestClient

from tests.conftest import CTGovStudyForTest


def test_stats_endpoint_success(client: TestClient, session):
    """Test that the stats endpoint returns database statistics."""
    # Add some test data
    study1 = CTGovStudyForTest(
        nct_id="NCT001",
        brief_title="Study 1",
        is_latest=True,
        overall_status="RECRUITING",
        study_type="INTERVENTIONAL",
    )
    study2 = CTGovStudyForTest(
        nct_id="NCT002",
        brief_title="Study 2",
        is_latest=True,
        overall_status="COMPLETED",
        study_type="OBSERVATIONAL",
    )
    session.add_all([study1, study2])
    session.commit()

    response = client.get("/stats")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert isinstance(data["total"], int)


def test_stats_endpoint_structure(client: TestClient, session):
    """Test that the stats endpoint returns the expected structure."""
    response = client.get("/stats")

    assert response.status_code == 200
    data = response.json()

    # Check required fields from the current implementation
    assert "total" in data
    assert "recruiting" in data
    assert "interventional" in data
    assert "observational" in data

    # Check types
    assert isinstance(data["total"], int)
    assert isinstance(data["recruiting"], int)
    assert isinstance(data["interventional"], int)
    assert isinstance(data["observational"], int)

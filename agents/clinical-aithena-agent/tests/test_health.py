"""Tests for the health endpoint."""

from fastapi.testclient import TestClient


def test_health_endpoint_success(client: TestClient):
    """Test that the health endpoint returns success with database connected."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "database" in data
    # SQLite test DB should connect successfully
    assert "error" not in data["database"]


def test_health_endpoint_structure(client: TestClient):
    """Test that the health endpoint returns the expected structure."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Check required fields are present
    assert "status" in data
    assert "database" in data

    # Check types
    assert isinstance(data["status"], str)
    assert isinstance(data["database"], str)


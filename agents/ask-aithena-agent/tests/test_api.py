from typing import Iterator
from fastapi import logger
import pytest
from fastapi.testclient import TestClient
from polus.aithena.ask_aithena.api import app
from polus.aithena.ask_aithena import AskAithenaQuery
from polus.aithena.common.logger import get_logger
import requests


@pytest.fixture(scope="module")
def test_client() -> Iterator[TestClient]:
    client = TestClient(app)
    yield client


def test_status(test_client: TestClient):
    """Test the agent is running."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ask-aithena agent is running"}


def test_ask_aithena(test_client: TestClient):
    """Test the ask_aithena endpoint."""
    # We are not running integration tests so this is expected to fail
    # as the embedding service is not running.
    query = AskAithenaQuery(query="What is the capital of France?")

    with pytest.raises(requests.RequestException) as excinfo:
        response = test_client.post(
            "/ask", json=query.model_dump(), params={"stream": "false"}
        )
        response.raise_for_status()
    print(f"Exception type: {excinfo.type}")
    print(f"Exception value: {excinfo.value}")

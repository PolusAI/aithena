"""Common test fixtures for OpenAlex API tests."""

import pytest
from unittest.mock import patch, MagicMock
import asyncio
from typing import Dict, Any, List

# Sample mock data
MOCK_WORKS_DATA = {
    "meta": {
        "count": 10,
        "db_response_time_ms": 42,
        "page": 1,
        "per_page": 5,
    },
    "results": [
        {
            "id": f"https://openalex.org/W{i}",
            "title": f"Test Work {i}",
            "publication_year": 2020 + (i % 3),
            "type": "journal-article",
            "authorships": [
                {
                    "author": {
                        "id": f"https://openalex.org/A{i*10}",
                        "display_name": f"Author {i*10}",
                    },
                    "institutions": [],
                }
            ],
            "biblio": {"volume": str(i), "issue": "1"},
            "concepts": [],
            "referenced_works": [],
            "related_works": [],
            "abstract_inverted_index": {},
        }
        for i in range(1, 6)
    ],
}

# More detailed single work data for specific tests
MOCK_SINGLE_WORK = {
    "id": "https://openalex.org/W123456789",
    "title": "A comprehensive study of something important",
    "publication_year": 2022,
    "type": "journal-article",
    "authorships": [
        {
            "author": {
                "id": "https://openalex.org/A987654321",
                "display_name": "Jane Doe",
            },
            "institutions": [
                {
                    "id": "https://openalex.org/I123",
                    "display_name": "University of Research",
                },
            ],
        },
        {
            "author": {
                "id": "https://openalex.org/A123456789",
                "display_name": "John Smith",
            },
            "institutions": [
                {"id": "https://openalex.org/I456", "display_name": "Tech Institute"},
            ],
        },
    ],
    "biblio": {"volume": "42", "issue": "3", "first_page": "100", "last_page": "115"},
    "concepts": [
        {
            "id": "https://openalex.org/C123",
            "display_name": "Machine Learning",
            "score": 0.9,
        },
        {
            "id": "https://openalex.org/C456",
            "display_name": "Data Science",
            "score": 0.8,
        },
    ],
    "referenced_works": ["https://openalex.org/W111", "https://openalex.org/W222"],
    "related_works": ["https://openalex.org/W333", "https://openalex.org/W444"],
    "abstract_inverted_index": {
        "study": [0],
        "comprehensive": [1],
        "important": [2],
    },
}

# Counter for API requests across all tests
MAX_API_REQUESTS = int(
    pytest.importorskip("os").environ.get("OPENALEX_API_MAX_REQUESTS", "500")
)
CURRENT_API_REQUESTS = 0


@pytest.fixture(autouse=True)
def check_api_request_limit():
    """Check if we've reached the maximum number of API requests."""
    global CURRENT_API_REQUESTS

    # Skip the check if MAX_API_REQUESTS is -1 (unlimited)
    if MAX_API_REQUESTS != -1 and CURRENT_API_REQUESTS >= MAX_API_REQUESTS:
        pytest.skip(
            f"Skipping test: Maximum API request limit ({MAX_API_REQUESTS}) reached"
        )

    # Patch the metrics_collector.record_request to count actual API requests
    with patch(
        "polus.aithena.jobs.getopenalex.rest.metrics_collector.record_request",
        side_effect=_count_and_record_request,
    ):
        yield


def _count_and_record_request(duration_ms, success=True, cached=False):
    """Count API requests and call the original record_request."""
    global CURRENT_API_REQUESTS

    # Only count non-cached requests (real API calls)
    if not cached:
        CURRENT_API_REQUESTS += 1

        # Print a warning when approaching the limit
        if MAX_API_REQUESTS != -1 and CURRENT_API_REQUESTS % 100 == 0:
            print(f"API Request count: {CURRENT_API_REQUESTS}/{MAX_API_REQUESTS}")

        # Skip if over the limit
        if MAX_API_REQUESTS != -1 and CURRENT_API_REQUESTS >= MAX_API_REQUESTS:
            pytest.skip(
                f"Maximum API request limit ({MAX_API_REQUESTS}) reached during test"
            )

    # Simply update the metrics directly instead of trying to call the original function
    from polus.aithena.jobs.getopenalex.rest.metrics import metrics_collector

    # Update metrics directly - simpler solution that doesn't rely on accessing __wrapped__
    metrics_collector.total_requests += 1
    if not success:
        metrics_collector.failed_requests += 1
    if cached:
        metrics_collector.cache_hits += 1
    else:
        metrics_collector.cache_misses += 1
    metrics_collector.request_times.append(duration_ms)


def pytest_sessionfinish(session, exitstatus):
    """Print total API requests after all tests have completed."""
    global CURRENT_API_REQUESTS
    print(f"\nTotal OpenAlex API requests made: {CURRENT_API_REQUESTS}")
    if MAX_API_REQUESTS != -1:
        print(f"Maximum allowed API requests: {MAX_API_REQUESTS}")
        print(f"Remaining API requests: {MAX_API_REQUESTS - CURRENT_API_REQUESTS}")


@pytest.fixture
def mock_works_response():
    """Return mock OpenAlex API works response data."""
    return MOCK_WORKS_DATA


@pytest.fixture
def mock_single_work():
    """Return detailed mock data for a single work."""
    return MOCK_SINGLE_WORK


@pytest.fixture
def mock_works_api():
    """Mock the Works API class for synchronous tests."""
    with patch("pyalex.Works") as mock_works:
        # Create the mock instance that will be returned
        works_instance = MagicMock()

        # Configure filter to return the instance itself for method chaining
        works_instance.filter.return_value = works_instance

        # Configure get method to return mock data
        works_instance.get.return_value = MOCK_WORKS_DATA

        # Configure paginate to yield pages of results
        works_instance.paginate.return_value = [
            [
                MagicMock(
                    **{
                        "__getitem__.side_effect": lambda k: MOCK_WORKS_DATA["results"][
                            i
                        ]
                    }
                )
                for i in range(5)
            ]
        ]

        # Set Works() to return our configured instance
        mock_works.return_value = works_instance

        yield mock_works


@pytest.fixture
def mock_pyalex_work():
    """Mock the PyalexWork class."""
    with patch("pyalex.Work") as mock_work:
        # Make the mock work like a dictionary for attribute access
        mock_work_instance = MagicMock()
        mock_work_instance.__getitem__.side_effect = lambda k: MOCK_SINGLE_WORK.get(k)
        mock_work.return_value = mock_work_instance
        yield mock_work


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

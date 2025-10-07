# OpenAlex REST API Tests

This directory contains tests for the OpenAlex REST API components.

## API Request Limiting

The test suite is configured to limit the total number of API requests to OpenAlex to a maximum of 500 by default. This is to:

1. Avoid excessive API usage during development and CI pipelines
2. Prevent hitting rate limits on the OpenAlex API
3. Keep tests running quickly by using mocks when possible

### How it works

- A global counter in `conftest.py` tracks the number of actual API requests made
- The maximum number of requests is configured via the `OPENALEX_API_MAX_REQUESTS` environment variable in `pytest.ini`
- Tests are automatically skipped when the limit is reached
- Every 100 requests, a message is printed showing the current count

### Changing the limit

You can change the limit by:

1. Modifying the value in `pytest.ini`
2. Setting the environment variable when running tests:

```bash
OPENALEX_API_MAX_REQUESTS=1000 pytest
```

### Running without a limit

To run without any limit (not recommended):

```bash
OPENALEX_API_MAX_REQUESTS=-1 pytest
```

### Troubleshooting

If you encounter test failures related to the request counting mechanism, check:

1. The `_count_and_record_request` function in `conftest.py` - this function handles counting API requests and properly updates the metrics collector
2. Assertions in test files that verify the correct behavior of the `record_request` method - note that this method is called with three positional arguments: `(duration_ms, success, cached)`

The API request counting mechanism works by patching the `metrics_collector.record_request` method, which allows it to track real API calls without interfering with normal test behavior.

## Test Structure

The tests are organized as follows:

- `test_rest_basics.py`: Tests for basic functionality of the REST API components
- `test_rest_integration.py`: Integration tests for the REST API modules
- `test_rest_paginator.py`: Tests for the paginator functionality
- `test_rest_works.py`: Tests for the works-related functionality

## Running the Tests

Run all tests:

```bash
pytest tests/rest
```

Run a specific test file:

```bash
pytest tests/rest/test_rest_basics.py
```

Run a specific test:

```bash
pytest tests/rest/test_rest_basics.py::TestMetricsCollector::test_record_request
```

## Mocking vs Real API Calls

Most tests should use mocks instead of making real API calls. Only use real API calls when specifically testing:

1. Real integration with the OpenAlex API
2. Network error handling
3. Rate limiting behavior

When writing new tests, prefer using the mock fixtures provided in `conftest.py`.

## Test Organization

- `conftest.py`: Contains common test fixtures
- `test_rest_basics.py`: Tests for basic components (context managers, wrappers, metrics)
- `test_rest_works.py`: Tests for work-related functions
- `test_rest_paginator.py`: Tests for paginator functionality
- `test_rest_integration.py`: Integration tests to verify modules work together

## Running Tests

To run all tests:

```bash
pytest src/polus/aithena/jobs/getopenalex/tests/
```

To run a specific test file:

```bash
pytest src/polus/aithena/jobs/getopenalex/tests/test_rest_basics.py
```

To run a specific test:

```bash
pytest src/polus/aithena/jobs/getopenalex/tests/test_rest_basics.py::TestMetricsCollector::test_record_request
```

To run tests with verbose output:

```bash
pytest -v src/polus/aithena/jobs/getopenalex/tests/
```

## Test Coverage

To run tests with coverage:

```bash
pytest --cov=polus.aithena.jobs.getopenalex.rest src/polus/aithena/jobs/getopenalex/tests/
```

## Notes

- These tests use mocks to avoid making actual API calls to OpenAlex.
- The tests cover both synchronous and asynchronous functionality.
- The integration tests demonstrate how different components work together. 
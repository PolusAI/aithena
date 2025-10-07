"""Tests for the basic OpenAlex REST API components."""

import time
import pytest
from unittest.mock import patch, MagicMock, call
import httpx
import asyncio

from polus.aithena.jobs.getopenalex.rest import (
    OpenAlexError,
    APIError,
    metrics_collector,
    api_session,
    async_api_session,
    with_metrics,
    with_retry,
)


class TestMetricsCollector:
    """Test the metrics collector functionality."""

    def test_record_request(self):
        """Test recording a request in the metrics collector."""
        # Reset the collector to start with a clean state
        metrics_collector.request_times = []
        metrics_collector.total_requests = 0
        metrics_collector.failed_requests = 0
        metrics_collector.cache_hits = 0
        metrics_collector.cache_misses = 0

        # Record successful request
        metrics_collector.record_request(100, success=True, cached=False)
        assert metrics_collector.total_requests == 1
        assert metrics_collector.failed_requests == 0
        assert metrics_collector.cache_hits == 0
        assert metrics_collector.cache_misses == 1
        assert metrics_collector.request_times == [100]

        # Record failed request
        metrics_collector.record_request(200, success=False, cached=False)
        assert metrics_collector.total_requests == 2
        assert metrics_collector.failed_requests == 1
        assert metrics_collector.cache_hits == 0
        assert metrics_collector.cache_misses == 2
        assert metrics_collector.request_times == [100, 200]

        # Record cached request
        metrics_collector.record_request(50, success=True, cached=True)
        assert metrics_collector.total_requests == 3
        assert metrics_collector.failed_requests == 1
        assert metrics_collector.cache_hits == 1
        assert metrics_collector.cache_misses == 2
        assert metrics_collector.request_times == [100, 200, 50]

    def test_session_lifecycle(self):
        """Test the session start and end functionality."""
        # Start a new session
        metrics_collector.start_session()
        assert metrics_collector.start_time is not None
        assert metrics_collector.end_time is None
        assert metrics_collector.total_requests == 0

        # Record some requests
        metrics_collector.record_request(100)
        metrics_collector.record_request(200)

        # End the session
        metrics_collector.end_session()
        assert metrics_collector.end_time is not None

        # Get summary
        summary = metrics_collector.get_summary()
        assert summary["total_requests"] == 2
        assert summary["failed_requests"] == 0
        assert summary["avg_request_time_ms"] == 150
        assert summary["min_request_time_ms"] == 100
        assert summary["max_request_time_ms"] == 200
        assert "total_duration_seconds" in summary
        assert "requests_per_second" in summary


class TestContextManagers:
    """Test context manager functionality."""

    def test_api_session(self):
        """Test the api_session context manager."""
        with patch.object(metrics_collector, "start_session") as mock_start:
            with patch.object(metrics_collector, "end_session") as mock_end:
                with patch.object(metrics_collector, "log_summary") as mock_log:
                    # Use the context manager
                    with api_session():
                        # Check that session was started
                        mock_start.assert_called_once()

                    # Check that session was ended and logged
                    mock_end.assert_called_once()
                    mock_log.assert_called_once()

    def test_api_session_with_metrics_disabled(self):
        """Test the api_session context manager with metrics disabled."""
        with patch.object(metrics_collector, "start_session") as mock_start:
            with patch.object(metrics_collector, "end_session") as mock_end:
                with patch.object(metrics_collector, "log_summary") as mock_log:
                    # Use the context manager with metrics disabled
                    with api_session(collect_metrics=False):
                        pass

                    # Check that no metrics methods were called
                    mock_start.assert_not_called()
                    mock_end.assert_not_called()
                    mock_log.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_api_session(self):
        """Test the async_api_session context manager."""
        with patch.object(metrics_collector, "start_session") as mock_start:
            with patch.object(metrics_collector, "end_session") as mock_end:
                with patch.object(metrics_collector, "log_summary") as mock_log:
                    # Use the async context manager
                    async with async_api_session():
                        # Check that session was started
                        mock_start.assert_called_once()

                    # Check that session was ended and logged
                    mock_end.assert_called_once()
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_api_session_with_metrics_disabled(self):
        """Test the async_api_session context manager with metrics disabled."""
        with patch.object(metrics_collector, "start_session") as mock_start:
            with patch.object(metrics_collector, "end_session") as mock_end:
                with patch.object(metrics_collector, "log_summary") as mock_log:
                    # Use the async context manager with metrics disabled
                    async with async_api_session(collect_metrics=False):
                        pass

                    # Check that no metrics methods were called
                    mock_start.assert_not_called()
                    mock_end.assert_not_called()
                    mock_log.assert_not_called()


class TestWrappers:
    """Test decorator and wrapper functionality."""

    def test_with_metrics_decorator(self):
        """Test the with_metrics decorator."""
        with patch.object(metrics_collector, "record_request") as mock_record:
            # Create a test function with the with_metrics decorator
            @with_metrics
            def test_func(a, b):
                return a + b

            # Call the function
            result = test_func(2, 3)

            # Check that the function works correctly
            assert result == 5

            # Check that metrics were recorded
            mock_record.assert_called_once()
            # Check that the function was called with correct arguments
            args, kwargs = mock_record.call_args
            assert len(args) == 3  # duration_ms, success, cached
            assert isinstance(args[0], float)  # duration_ms
            assert args[1] is True  # success
            assert args[2] is False  # cached
            assert kwargs == {}

    def test_with_metrics_decorator_on_exception(self):
        """Test the with_metrics decorator when the wrapped function raises an exception."""
        with patch.object(metrics_collector, "record_request") as mock_record:
            # Create a test function with the with_metrics decorator that raises an exception
            @with_metrics
            def test_func_error():
                raise ValueError("Test error")

            # Call the function and expect an exception
            with pytest.raises(ValueError):
                test_func_error()

            # Check that metrics were recorded with success=False
            mock_record.assert_called_once()
            args, kwargs = mock_record.call_args
            assert len(args) == 3
            assert isinstance(args[0], float)
            assert args[1] is False  # success=False
            assert args[2] is False  # cached=False
            assert kwargs == {}

    def test_with_retry_decorator_success(self):
        """Test the with_retry decorator when the function succeeds."""
        # Create a mock function to be decorated
        mock_func = MagicMock(return_value="success")

        # Apply the with_retry decorator
        decorated_func = with_retry(mock_func)

        # Call the decorated function
        result = decorated_func(1, 2, key="value")

        # Check that the original function was called once with the correct arguments
        mock_func.assert_called_once_with(1, 2, key="value")
        assert result == "success"

    def test_with_retry_decorator_with_retries(self):
        """Test the with_retry decorator when the function fails and then succeeds."""
        # Create a mock function that fails twice then succeeds
        mock_func = MagicMock(
            side_effect=[APIError("Test error 1"), APIError("Test error 2"), "success"]
        )

        # Mock sleep to avoid delays in tests
        with patch("time.sleep") as mock_sleep:
            # Apply the with_retry decorator
            decorated_func = with_retry(mock_func)

            # Call the decorated function
            result = decorated_func()

            # Check that the original function was called three times
            assert mock_func.call_count == 3
            # Check that sleep was called twice with expected backoff times
            mock_sleep.assert_has_calls([call(1), call(2)])
            assert result == "success"

    def test_with_retry_decorator_all_failures(self):
        """Test the with_retry decorator when all retries fail."""
        # Create a mock function that always raises an exception
        mock_func = MagicMock(side_effect=APIError("Test error"))

        # Mock sleep to avoid delays in tests
        with patch("time.sleep") as mock_sleep:
            # Apply the with_retry decorator
            decorated_func = with_retry(mock_func)

            # Call the decorated function and expect an exception
            with pytest.raises(OpenAlexError):
                decorated_func()

            # Check that the original function was called MAX_RETRIES times
            assert mock_func.call_count == 3  # Assuming MAX_RETRIES = 3
            # Check that sleep was called the expected number of times
            assert mock_sleep.call_count == 3

    def test_with_retry_decorator_with_httpx_error(self):
        """Test the with_retry decorator with httpx errors."""
        # Create a mock function that raises httpx.HTTPError
        mock_func = MagicMock(
            side_effect=[httpx.HTTPError("Test HTTP error"), "success"]
        )

        # Mock sleep to avoid delays in tests
        with patch("time.sleep") as mock_sleep:
            # Apply the with_retry decorator
            decorated_func = with_retry(mock_func)

            # Call the decorated function
            result = decorated_func()

            # Check that the original function was called twice
            assert mock_func.call_count == 2
            # Check that sleep was called once
            mock_sleep.assert_called_once_with(1)
            assert result == "success"

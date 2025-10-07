"""Context managers for the OpenAlex REST API."""

# Standard library imports
import contextlib
from collections.abc import AsyncIterator
from collections.abc import Iterator

import aiohttp

# Local imports
from polus.aithena.jobs.getopenalex.logger import get_logger

from .common import API_REQUEST_TIMEOUT
from .metrics import metrics_collector

logger = get_logger(__name__)


@contextlib.contextmanager
def api_session(collect_metrics: bool = True) -> Iterator[None]:
    """Context manager for API sessions with optional metrics collection.

    Args:
        collect_metrics: Whether to collect performance metrics

    Yields:
        None
    """
    if collect_metrics:
        metrics_collector.start_session()

    try:
        yield
    finally:
        if collect_metrics:
            metrics_collector.end_session()
            metrics_collector.log_summary()


@contextlib.asynccontextmanager
async def async_api_session(
    collect_metrics: bool = True,
    timeout: float | None = None,
) -> AsyncIterator[aiohttp.ClientSession]:
    """Async context manager for API sessions with optional metrics collection.

    Creates and yields an aiohttp.ClientSession with proper timeout settings.

    Args:
        collect_metrics: Whether to collect performance metrics
        timeout: Custom timeout in seconds (uses DEFAULT_TIMEOUT if None)

    Yields:
        aiohttp.ClientSession: Client session for making HTTP requests
    """
    if collect_metrics:
        metrics_collector.start_session()

    # Use provided timeout or default
    timeout_value = timeout if timeout is not None else API_REQUEST_TIMEOUT

    # Create timeout object
    timeout_obj = aiohttp.ClientTimeout(total=timeout_value)

    # Create session with timeout
    session = aiohttp.ClientSession(timeout=timeout_obj)

    try:
        yield session
    finally:
        # Close the session
        await session.close()

        if collect_metrics:
            metrics_collector.end_session()
            metrics_collector.log_summary()

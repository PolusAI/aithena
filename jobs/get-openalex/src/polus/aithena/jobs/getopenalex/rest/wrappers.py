"""Wrappers for the OpenAlex REST API."""

# Standard library imports
import functools
import time
from collections.abc import Callable
from typing import ParamSpec
from typing import TypeVar

# Third-party imports
import httpx
import requests  # Import requests library

from polus.aithena.jobs.getopenalex.logger import get_logger

from .common import MAX_RETRIES
from .common import APIError

# Local imports
from .common import OpenAlexError
from .metrics import metrics_collector

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def with_metrics(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to track metrics for a function.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with metrics tracking
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        success = True
        cached = False

        try:
            return func(*args, **kwargs)
        except Exception:
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_request(duration_ms, success, cached)

    return wrapper


def with_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to retry API calls with exponential backoff.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with retry logic
    """

    @functools.wraps(func)
    @with_metrics  # Apply metrics decorator *after* wraps
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        retries = 0
        while retries < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            # Catch both httpx errors (for async) and requests errors (for sync pyalex)
            except (
                httpx.HTTPError,
                requests.exceptions.RequestException,
                APIError,
            ) as e:
                wait_time = 2**retries
                logger.warning(
                    f"API call failed: {e}. Retrying in {wait_time}s... "
                    f"(Attempt {retries + 1}/{MAX_RETRIES})",
                )
                time.sleep(wait_time)
                retries += 1
        # If we get here, all retries failed
        raise OpenAlexError(f"Failed after {MAX_RETRIES} retries")

    return wrapper

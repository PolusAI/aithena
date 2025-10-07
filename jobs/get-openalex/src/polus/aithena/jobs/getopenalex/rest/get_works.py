"""Get works from the OpenAlex REST API."""

# Standard library imports
import asyncio
import http
import time
from collections.abc import AsyncIterator
from collections.abc import Iterator
from functools import lru_cache
from itertools import chain
from typing import Any

# Third-party imports
import pyalex
from openalex_types import Work
from pyalex import Work as PyalexWork
from pyalex import Works

from polus.aithena.jobs.getopenalex.logger import get_logger
from polus.aithena.jobs.getopenalex.config import OPENALEX_API_KEY
from polus.aithena.jobs.getopenalex.config import PYALEX_EMAIL

from .common import API_REQUEST_TIMEOUT
from .common import RATE_LIMIT_DELAY
from .common import APIError

# Local imports
from .common import OpenAlexError
from .common import RateLimitError
from .context import async_api_session
from .metrics import metrics_collector

# Import PaginatorOptions from paginator module
from .wrappers import with_retry

logger = get_logger(__name__)

# Constants
OPENALEX_PER_PAGE_LIMIT = 200  # Max per_page allowed by OpenAlex API
OFFSET_PAGINATION_LIMIT = 10000  # Max results for offset pagination

# HTTP Status Codes
HTTP_OK = http.HTTPStatus.OK
HTTP_TOO_MANY_REQUESTS = http.HTTPStatus.TOO_MANY_REQUESTS

# Configure pyalex email and timeout using values from config.py
pyalex.config.email = PYALEX_EMAIL  # Use PYALEX_EMAIL directly from config
pyalex.config.timeout = API_REQUEST_TIMEOUT  # Use API_REQUEST_TIMEOUT from config


@lru_cache(maxsize=128)
def get_filtered_works(
    filters_tuple: tuple,  # Convert dict to tuple for hashability
    per_page: int = 25,
    max_results: int | None = None,
    cursor_based: bool = True,
    convert_to_model: bool = True,
) -> list[Work | PyalexWork]:
    """Get a list of works filtered by the given criteria.

    Results are cached based on the input parameters.

    Args:
        filters_tuple: Tuple representation of filters dictionary
        per_page: Number of results per page (default: 25).
        max_results: Maximum results to return (default: None).
        cursor_based: Use cursor (True) or offset (False) pagination.
                      Cursor-based recommended for >10k results.
        convert_to_model: Convert PyalexWork objects to Work models.

    Returns:
        list[Work | PyalexWork]: List of Work or PyalexWork objects
    """
    # Convert tuple back to dictionary for use
    filters = dict(filters_tuple)

    # Record cache hit
    metrics_collector.record_request(0, success=True, cached=True)

    logger.info(f"Fetching works with filters: {filters}, max_results: {max_results}")

    try:
        if cursor_based:
            results = list(
                iter_filtered_works_cursor(
                    filters,
                    per_page,
                    max_results,
                    convert_to_model,
                ),
            )
        else:
            results = list(
                iter_filtered_works_offset(
                    filters,
                    per_page,
                    max_results,
                    convert_to_model,
                ),
            )

        logger.info(f"Retrieved {len(results)} works")
        return results
    except Exception as e:
        logger.error(f"Error retrieving works: {e}")
        raise OpenAlexError(f"Failed to retrieve works: {e!s}") from e


def get_filtered_works_dict(
    filters: dict[str, Any],
    per_page: int = 25,
    max_results: int | None = None,
    cursor_based: bool = True,
    convert_to_model: bool = True,
) -> list[Work | PyalexWork]:
    """Wrapper around get_filtered_works that accepts a dictionary for filters.

    This function converts the dict to a tuple for caching purposes.

    Args:
        filters: Dictionary of filters to apply
        per_page: Number of results per page (default: 25)
        max_results: Maximum number of results to return (default: None, returns all)
        cursor_based: Whether to use cursor-based pagination
        convert_to_model: Whether to convert PyalexWork objects to models

    Returns:
        list[Work | PyalexWork]: List of Work or PyalexWork objects
    """
    # Convert dict to sorted tuple of items for hashability
    filters_tuple = tuple(sorted(filters.items()))
    return get_filtered_works(
        filters_tuple=filters_tuple,
        per_page=per_page,
        max_results=max_results,
        cursor_based=cursor_based,
        convert_to_model=convert_to_model,
    )


def pyalex_to_model(work: PyalexWork) -> Work:
    """Convert a PyalexWork object to an openalex_types.Work model.

    Args:
        work: PyalexWork object to convert

    Returns:
        Work model
    """
    try:
        # The work object already contains the data, not need to call get()
        # Just convert it directly to a dictionary
        work_data = work

        # Handle datetime conversion to suppress warnings
        # Use model_validate(strict=False) for automatic string date conversion
        return Work.model_validate(work_data, strict=False)
    except Exception as e:
        logger.error(f"Error converting PyalexWork to Work model: {e}")
        raise OpenAlexError(f"Model conversion error: {e!s}") from e


def _process_work(work: PyalexWork, convert_to_model: bool) -> Work | PyalexWork:
    """Process a work object, optionally converting to a model.

    Centralizes the conversion logic for reuse.

    Args:
        work: The PyalexWork object to process
        convert_to_model: Whether to convert to Work model

    Returns:
        Either the original PyalexWork or a converted Work model
    """
    if convert_to_model:
        return pyalex_to_model(work)
    return work


# Function to validate and sanitize pagination parameters
def _validate_pagination_params(per_page: int, max_results: int | None) -> tuple:
    """Validate and sanitize pagination parameters.

    Args:
        per_page: Number of results per page
        max_results: Maximum number of results to return

    Returns:
        Tuple of (per_page, max_results)
    """
    # Ensure per_page is within reasonable bounds
    if per_page < 1:
        logger.warning(f"Invalid per_page value {per_page}, using default of 25")
        per_page = 25
    elif per_page > OPENALEX_PER_PAGE_LIMIT:
        logger.warning(
            f"per_page {per_page} > limit ({OPENALEX_PER_PAGE_LIMIT}), capping.",
        )
        per_page = OPENALEX_PER_PAGE_LIMIT

    # Ensure max_results is valid if specified
    if max_results is not None and max_results < 1:
        logger.warning(f"Invalid max_results value {max_results}, removing limit")
        max_results = None

    return per_page, max_results


@with_retry
def iter_filtered_works_cursor(
    filters: dict[str, Any],
    per_page: int = 25,
    max_results: int | None = None,
    convert_to_model: bool = False,
) -> Iterator[Work | PyalexWork]:
    """Iterator for works using cursor-based pagination.

    Recommended for large result sets (>10,000 items).

    Args:
        filters: Dictionary of filters to apply
        per_page: Number of results per page (default: 25)
        max_results: Maximum number of results to return (default: None, returns all)
        convert_to_model: Whether to convert PyalexWork objects to Work models.

    Yields:
        Individual Work or PyalexWork objects
    """
    per_page, max_results = _validate_pagination_params(per_page, max_results)
    query = Works().filter(**filters)

    # Set n_max to None to retrieve all results, or to a specific number to limit
    n_max = max_results

    try:
        # Use chain to flatten the pages into a single iterator of records
        for i, work in enumerate(
            chain.from_iterable(query.paginate(per_page=per_page, n_max=n_max)),
        ):
            if max_results is not None and i >= max_results:
                break

            yield _process_work(work, convert_to_model)
    except Exception as e:
        logger.error(f"Error in cursor-based pagination: {e}")
        raise APIError(f"Pagination error: {e!s}") from e


@with_retry
def iter_filtered_works_offset(
    filters: dict[str, Any],
    per_page: int = 25,
    max_results: int | None = None,
    convert_to_model: bool = False,
) -> Iterator[Work | PyalexWork]:
    """Iterator for works using offset-based pagination.

    Limited to 10,000 results by the OpenAlex API.

    Args:
        filters: Dictionary of filters to apply.
        per_page: Number of results per page (default: 25).
        max_results: Max results (default: None, returns all available).
        convert_to_model: Convert PyalexWork objects to Work models.

    Yields:
        Individual Work or PyalexWork objects
    """
    per_page, max_results = _validate_pagination_params(per_page, max_results)
    query = Works().filter(**filters)

    # Default to OFFSET_PAGINATION_LIMIT if max_results is None
    # Otherwise use the smaller of max_results or OFFSET_PAGINATION_LIMIT
    limit = (
        min(OFFSET_PAGINATION_LIMIT, max_results)
        if max_results is not None
        else OFFSET_PAGINATION_LIMIT
    )

    count = 0
    page = 1

    while True:
        try:
            # Get the current page of results
            results = query.get(page=page, per_page=per_page)

            # Stop if no results
            if not results or "results" not in results or not results["results"]:
                break

            # Yield each work in the results
            for work_data in results["results"]:
                count += 1
                if count > limit:
                    return

                work = PyalexWork(work_data)
                yield _process_work(work, convert_to_model)

            # Move to next page
            page += 1

            # Respect rate limits with a small delay between pages
            time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            logger.error(f"Error in offset-based pagination at page {page}: {e}")
            raise APIError(f"Pagination error at page {page}: {e!s}") from e


@with_retry
def get_works_page(
    filters: dict[str, Any],
    page: int = 1,
    per_page: int = 25,
    cursor: str | None = None,
    convert_to_model: bool = True,
) -> dict[str, Any]:
    """Get a single page of works.

    Args:
        filters: Dictionary of filters to apply
        page: Page number for offset-based pagination
        per_page: Number of results per page
        cursor: Cursor string for cursor-based pagination
        convert_to_model: Whether to convert results to openalex_types.Work models

    Returns:
        Dictionary containing the page results and metadata
    """
    per_page, _ = _validate_pagination_params(per_page, None)
    query = Works().filter(**filters)

    try:
        if cursor:
            # Cursor-based pagination
            results = query.get(per_page=per_page, cursor=cursor)
        else:
            # Offset-based pagination
            results = query.get(page=page, per_page=per_page)

        # Convert results if requested
        if convert_to_model and "results" in results:
            results["results"] = [
                pyalex_to_model(PyalexWork(work)).model_dump()
                for work in results["results"]
            ]

        return results
    except Exception as e:
        logger.error(f"Error getting works page: {e}")
        raise APIError(f"Failed to get works page: {e!s}") from e


# Async implementations for improved performance


async def get_filtered_works_async(
    filters: dict[str, Any],
    per_page: int = 25,
    max_results: int | None = None,
    convert_to_model: bool = True,
) -> list[Work | PyalexWork]:
    """Asynchronous version of get_filtered_works.

    Return all works that match the given filters, up to max_results.

    Args:
        filters: Dictionary of filters to apply
        per_page: Number of results per page (default: 25)
        max_results: Maximum number of results to return (default: None, returns all)
        convert_to_model: Whether to convert PyalexWork objects to Work models.

    Returns:
        list[Work | PyalexWork]: List of Work or PyalexWork objects
    """
    logger.info(
        f"Fetching works async with filters: {filters}, max_results: {max_results}",
    )

    try:
        # Set a strict timeout (double request timeout)
        timeout = API_REQUEST_TIMEOUT * 2

        # Wrap the async iterator in a timeout
        async with asyncio.timeout(timeout):
            works = []
            async for work in iter_filtered_works_async(
                filters,
                per_page,
                max_results,
                convert_to_model,
            ):
                works.append(work)

                # If we've reached max_results, stop early
                if max_results is not None and len(works) >= max_results:
                    break

            logger.info(f"Retrieved {len(works)} works asynchronously")
            return works

    except TimeoutError as e:
        logger.error(
            f"Timeout after {timeout} seconds while fetching works from OpenAlex",
        )
        raise APIError(
            f"Timeout while fetching works from OpenAlex (after {timeout}s)",
        ) from e
    except Exception as e:
        logger.error(f"Error retrieving works asynchronously: {e}")
        raise OpenAlexError(f"Failed to retrieve works asynchronously: {e!s}") from e


async def iter_filtered_works_async(
    filters: dict[str, Any],
    per_page: int = 25,
    max_results: int | None = None,
    convert_to_model: bool = False,
) -> AsyncIterator[Work | PyalexWork]:
    """Asynchronous iterator for filtered works.

    Retrieves works asynchronously in batches for efficiency.

    Args:
        filters: Dictionary of filters to apply
        per_page: Number of results per page (default: 25)
        max_results: Maximum number of results to return (default: None, returns all)
        convert_to_model: Whether to convert PyalexWork objects to Work models.

    Yields:
        Individual Work or PyalexWork objects
    """
    per_page, max_results = _validate_pagination_params(per_page, max_results)

    # Set per_page to an optimal value for batching
    per_page = min(per_page, 100)  # Limit to 100 per batch

    count_yielded = 0
    cursor = None

    # Implement pagination logic with cursor
    try:
        while True:
            # Set a timeout for each individual API request
            try:
                async with asyncio.timeout(API_REQUEST_TIMEOUT):  # Use config timeout
                    response = await get_filtered_works_dict_async(
                        filters=filters,
                        per_page=per_page,
                        cursor=cursor,
                    )
            except TimeoutError as e:
                logger.error(
                    f"Timeout after {API_REQUEST_TIMEOUT}s fetching page from OpenAlex",
                )
                err_msg = f"Timeout fetching page after {API_REQUEST_TIMEOUT}s"
                raise APIError(err_msg) from e

            # Extract works from response
            if not response or "results" not in response:
                logger.warning("No results found in OpenAlex response")
                break

            works = response.get("results", [])

            if not works:
                break

            # Get cursor for next page if available
            cursor = response.get("meta", {}).get("next_cursor")

            # Process and yield works
            for work in works:
                if convert_to_model:
                    yield pyalex_to_model(work)
                else:
                    yield work

                count_yielded += 1

                # Check if we've reached the maximum
                if max_results is not None and count_yielded >= max_results:
                    return

            # If no cursor, we've reached the end
            if not cursor:
                break

    except Exception as e:
        logger.error(f"Error in async iterator: {e}")
        raise OpenAlexError(f"Error in async works iterator: {e!s}") from e


# Helper function to build parameters for async dict request
def _build_async_dict_params(
    filters: dict[str, Any],
    page: int,
    per_page: int,
    cursor: str | None,
    api_key: str | None,
    search: str | None,
) -> dict[str, Any]:
    """Build parameters dictionary for the async request."""
    params = {"per_page": per_page}
    if cursor:
        params["cursor"] = cursor
    else:
        params["page"] = page
    if search:
        params["search"] = search
    if api_key or OPENALEX_API_KEY:
        params["api_key"] = api_key or OPENALEX_API_KEY

    filter_parts = [f"{key}:{value}" for key, value in filters.items()]
    if filter_parts:
        params["filter"] = ",".join(filter_parts)
    return params


async def get_filtered_works_dict_async(
    filters: dict[str, Any],
    page: int = 1,
    per_page: int = 25,
    cursor: str | None = None,
    api_key: str | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """Asynchronous function to get a page of works from the OpenAlex API.

    Args:
        filters: Dictionary of filters to apply.
        page: Page number (for offset-based pagination).
        per_page: Results per page.
        cursor: Cursor for cursor-based pagination.
        api_key: OpenAlex API key (optional).
        search: Search query (optional).

    Returns:
        Dictionary with results and metadata.
    """
    base_url = "https://api.openalex.org/works"
    params = _build_async_dict_params(
        filters,
        page,
        per_page,
        cursor,
        api_key,
        search,
    )

    # Log the request (without API key)
    log_params = params.copy()
    if "api_key" in log_params:
        log_params["api_key"] = "***"
    logger.debug(f"Making async API request to {base_url} with params {log_params}")

    # Track the request start time for metrics
    start_time = time.time()

    try:
        async with async_api_session() as session:
            # Set a timeout for the HTTP request
            timeout = API_REQUEST_TIMEOUT  # Use config timeout

            try:
                async with session.get(
                    base_url,
                    params=params,
                    timeout=timeout,
                ) as response:
                    if response.status == HTTP_TOO_MANY_REQUESTS:
                        # Handle rate limiting
                        metrics_collector.record_request(
                            time.time() - start_time,
                            success=False,
                            rate_limited=True,
                        )
                        logger.warning(
                            "Rate limit exceeded in async call to OpenAlex API",
                        )
                        await asyncio.sleep(RATE_LIMIT_DELAY)
                        raise RateLimitError("OpenAlex API rate limit exceeded")

                    if response.status != HTTP_OK:
                        # Handle other HTTP errors
                        error_text = await response.text()
                        metrics_collector.record_request(
                            time.time() - start_time,
                            success=False,
                        )
                        logger.error(
                            f"OpenAlex API error: {response.status} - {error_text}",
                        )
                        err_msg = (
                            f"API status {response.status}: " f"{error_text[:60]}..."
                        )
                        raise APIError(err_msg)

                    # Parse JSON response
                    result = await response.json()
                    metrics_collector.record_request(
                        time.time() - start_time,
                        success=True,
                    )
                    return result

            except TimeoutError as e:
                metrics_collector.record_request(
                    time.time() - start_time,
                    success=False,
                )
                msg = f"Timeout after {API_REQUEST_TIMEOUT}s in async call"
                logger.error(msg)
                err_msg = f"Timeout in async call (after {API_REQUEST_TIMEOUT}s)"
                raise APIError(err_msg) from e

    except Exception as e:
        if not isinstance(e, RateLimitError | APIError):  # Don't log twice
            metrics_collector.record_request(time.time() - start_time, success=False)
            logger.error(f"Error in async API request: {e!s}")
        raise

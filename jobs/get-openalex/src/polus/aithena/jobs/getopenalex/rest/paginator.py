"""Paginator for the OpenAlex REST API."""

# Standard library imports
import asyncio
import http
import time
from collections.abc import AsyncIterator
from collections.abc import Iterator
from typing import Annotated
from typing import Any

from openalex_types import Work
from pyalex import Work as PyalexWork
from pyalex import Works

# Third-party imports
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import ValidationError

from polus.aithena.jobs.getopenalex.logger import get_logger

from .common import RATE_LIMIT_DELAY

# Local imports
from .common import APIError
from .common import OpenAlexError
from .context import async_api_session
from .metrics import metrics_collector

logger = get_logger(__name__)


# Create a Pydantic model for pagination options
class PaginatorOptions(BaseModel):
    """Configuration options for pagination."""

    filters: dict[str, Any]
    per_page: Annotated[int, Field(ge=1, le=200)] = 25
    max_results: int | None = None
    cursor_based: bool = True
    convert_to_model: bool = True
    async_enabled: bool = False
    collect_metrics: bool = True
    strict_mode: bool = False  # Whether to strictly enforce model validation
    raw: bool = False  # Whether to return raw PyalexWork objects

    model_config = ConfigDict(
        extra="forbid",  # Prevent extra fields
    )


# Define a helper function to convert PyalexWork to Work model
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

        # Use model_validate with strict=False to allow automatic conversion
        # of string dates to datetime
        return Work.model_validate(work_data, strict=False)
    except (ValidationError, TypeError, ValueError) as e:
        logger.error(f"Error converting PyalexWork to Work model: {e}")
        raise OpenAlexError(f"Model conversion error: {e!s}") from e


# Forward declarations for iter_filtered functions
# These will be imported properly in __init__.py
iter_filtered_works_cursor = None
iter_filtered_works_offset = None
iter_filtered_works_async = None


class WorksPaginator(BaseModel):
    """Class to handle pagination of works with both cursor and offset-based methods."""

    options: PaginatorOptions
    current_page: int = 1
    count: int | None = None
    has_next: bool = True
    search: str | None = None  # Add search as a public field

    # Use ConfigDict for Pydantic v2
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Private attribute for query - won't be included in serialization
    _query: Works | None = None  # Use Optional for clarity

    def __init__(self, **data: dict[str, Any]) -> None:
        """Initialize the WorksPaginator."""
        # If individual parameters are provided, convert them to options
        if "options" not in data and "filters" in data:
            options_data = {}
            for field in PaginatorOptions.model_fields:
                if field in data:
                    options_data[field] = data.pop(field)
            data["options"] = PaginatorOptions(**options_data)

        # Handle initial_page parameter if provided
        if "initial_page" in data:
            data["current_page"] = data.pop("initial_page")

        super().__init__(**data)

        # Initialize query with filters
        self._query = Works().filter(**self.options.filters)

        # Add search parameter if provided
        if self.search:
            self._query = self._query.search(self.search)

    @property
    def query(self) -> Works:
        """Access the query object."""
        if self._query is None:
            self._query = Works().filter(**self.options.filters)
            if self.search:
                self._query = self._query.search(self.search)
        return self._query

    @property
    def filters(self) -> dict[str, Any]:
        """Access filters from options."""
        return self.options.filters

    @property
    def per_page(self) -> int:
        """Access per_page from options."""
        return self.options.per_page

    @property
    def max_results(self) -> int | None:
        """Access max_results from options."""
        return self.options.max_results

    @property
    def cursor_based(self) -> bool:
        """Access cursor_based from options."""
        return self.options.cursor_based

    @property
    def convert_to_model(self) -> bool:
        """Access convert_to_model from options."""
        return self.options.convert_to_model

    @property
    def async_enabled(self) -> bool:
        """Access async_enabled from options."""
        return self.options.async_enabled

    @property
    def collect_metrics(self) -> bool:
        """Access collect_metrics from options."""
        return self.options.collect_metrics

    @property
    def strict_mode(self) -> bool:
        """Access strict_mode from options."""
        return self.options.strict_mode

    @property
    def raw(self) -> bool:
        """Access raw from options."""
        return self.options.raw

    @property
    def total_pages(self) -> int | None:
        """Calculate the total number of pages based on the count and per_page.

        Returns:
            Optional[int]: The total number of pages, or None if count is not available.
        """
        if self.count is None:
            return None

        return (self.count + self.per_page - 1) // self.per_page

    def __iter__(self) -> Iterator[Work | PyalexWork]:
        """Iterate over all works matching the filters.

        Returns:
            Iterator yielding individual works
        """
        # Import here to avoid circular imports
        from .get_works import iter_filtered_works_cursor
        from .get_works import iter_filtered_works_offset

        if self.cursor_based:
            yield from iter_filtered_works_cursor(
                self.filters,
                self.per_page,
                self.max_results,
                self.convert_to_model,
            )
        else:
            yield from iter_filtered_works_offset(
                self.filters,
                self.per_page,
                self.max_results,
                self.convert_to_model,
            )

    async def iter_async(self) -> AsyncIterator[Work | PyalexWork]:
        """Asynchronously iterate over all works matching the filters.

        Returns:
            Async iterator yielding individual works
        """
        # Import here to avoid circular imports
        from .get_works import iter_filtered_works_async

        async for work in iter_filtered_works_async(
            self.filters,
            self.per_page,
            self.max_results,
            self.convert_to_model,
        ):
            yield work

    def iter_pages(self) -> Iterator[list[Work | PyalexWork]]:
        """Iterate over pages of works.

        Returns:
            Iterator yielding lists of works, where each list is a page
        """
        if self.cursor_based:
            # Use the paginate method for cursor-based pagination
            for page in self.query.paginate(
                per_page=self.per_page,
                n_max=self.max_results,
            ):
                if self.convert_to_model and not self.raw:  # Check raw flag
                    yield [pyalex_to_model(work) for work in page]
                else:
                    yield page
        else:
            # Implement offset-based pagination manually
            page_num = 1
            total_yielded = 0

            while True:
                try:
                    results = self.query.get(page=page_num, per_page=self.per_page)

                    if (
                        not results
                        or "results" not in results
                        or not results["results"]
                    ):
                        break

                    if self.convert_to_model and not self.raw:  # Check raw flag
                        page_items = [
                            pyalex_to_model(PyalexWork(work))
                            for work in results["results"]
                        ]
                    else:
                        page_items = [PyalexWork(work) for work in results["results"]]

                    yield page_items

                    total_yielded += len(page_items)
                    if (
                        self.max_results is not None
                        and total_yielded >= self.max_results
                    ):
                        break

                    page_num += 1

                    # Respect rate limits
                    time.sleep(RATE_LIMIT_DELAY)

                except APIError as e:  # Catch specific APIError
                    logger.error(f"Error in paginator at page {page_num}: {e}")
                    raise APIError(f"Pagination error at page {page_num}: {e!s}") from e

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the paginator and its metrics.

        Returns:
            Dictionary with paginator info and metrics
        """
        summary = {
            "filters": self.filters,
            "per_page": self.per_page,
            "max_results": self.max_results,
            "cursor_based": self.cursor_based,
            "convert_to_model": self.convert_to_model,
            "async_enabled": self.async_enabled,
        }

        if self.collect_metrics:
            summary["metrics"] = metrics_collector.get_summary()

        return summary

    def _build_async_page_params(self) -> dict[str, Any]:
        """Build parameters for the async page request."""
        params = {
            "page": self.current_page,
            "per_page": self.per_page,
        }
        if self.search:
            params["search"] = self.search

        filter_parts = []
        for key, value in self.filters.items():
            filter_parts.append(f"{key}:{value}")
        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        return params

    async def _make_async_request(
        self,
        params: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        """Make the asynchronous HTTP request."""
        url = "https://api.openalex.org/works"
        async with async_api_session(timeout=timeout) as session:
            async with session.get(url, params=params, timeout=timeout) as response:
                if response.status != http.HTTPStatus.OK:
                    error_text = await response.text()
                    logger.error(
                        f"OpenAlex API error: {response.status} - {error_text}",
                    )
                    raise APIError(f"OpenAlex API returned status {response.status}")
                return await response.json()

    def _process_async_response(
        self,
        result: dict[str, Any],
    ) -> list[Work | PyalexWork]:
        """Process the JSON response from the async request."""
        # Update pagination info
        meta = result.get("meta", {})
        self.count = meta.get("count", 0)
        self.current_page = meta.get("page", self.current_page)
        if self.total_pages:
            self.has_next = self.current_page < self.total_pages
        else:
            self.has_next = bool(meta.get("next_page"))

        # Process results
        if not result or "results" not in result:
            logger.warning(f"No results found for page {self.current_page}")
            return []

        processed_results = []
        for work_data in result.get("results", []):
            work = PyalexWork(work_data)
            if self.convert_to_model and not self.raw:  # Check raw flag
                try:
                    work = pyalex_to_model(work)
                except (ValidationError, TypeError, ValueError) as e:
                    logger.warning(f"Error converting work to model: {e}")
                    if self.options.strict_mode:
                        continue  # Skip if strict
            processed_results.append(work)

        msg = f"Retrieved {len(processed_results)} works for page {self.current_page}"
        logger.info(msg)
        return processed_results

    async def get_page_async(self) -> list[Work | PyalexWork]:
        """Asynchronously get the current page of works.

        Returns:
            List of Work objects for the current page.
        """
        timeout = 15.0  # Use a reasonable timeout for the overall operation
        try:
            async with asyncio.timeout(timeout):
                logger.info(
                    f"Fetching page {self.current_page} for search={self.search}, "
                    f"filters={self.filters}",
                )
                params = self._build_async_page_params()
                result = await self._make_async_request(params, timeout)
                return self._process_async_response(result)

        except TimeoutError as e:
            logger.error(
                f"Timeout after {timeout}s while fetching page {self.current_page}",
            )
            raise APIError(
                f"Timeout while fetching page {self.current_page} (after {timeout}s)",
            ) from e
        except (APIError, ValidationError, TypeError, ValueError) as e:
            logger.error(f"Error fetching page {self.current_page}: {e!s}")
            # Reraise as APIError for consistent handling upstream
            raise APIError(f"Error fetching page {self.current_page}: {e!s}") from e

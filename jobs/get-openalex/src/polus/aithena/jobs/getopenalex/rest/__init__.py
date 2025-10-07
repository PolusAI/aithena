"""REST API client for OpenAlex data."""

# Re-export key classes and functions from submodules
from .common import MAX_RETRIES
from .common import RATE_LIMIT_DELAY
from .common import APIError
from .common import OpenAlexError
from .common import RateLimitError
from .context import api_session
from .context import async_api_session

# Now import from get_works
from .get_works import get_filtered_works
from .get_works import get_filtered_works_async
from .get_works import get_filtered_works_dict
from .get_works import iter_filtered_works_async
from .get_works import iter_filtered_works_cursor
from .get_works import iter_filtered_works_offset
from .get_works import pyalex_to_model
from .metrics import metrics_collector

# Import from paginator first to avoid circular imports
from .paginator import PaginatorOptions
from .paginator import WorksPaginator

# Define __all__ in sorted order directly
__all__ = [
    "MAX_RETRIES",
    "RATE_LIMIT_DELAY",
    "APIError",
    "OpenAlexError",
    "PaginatorOptions",
    "RateLimitError",
    "WorksPaginator",
    "api_session",
    "async_api_session",
    "get_filtered_works",
    "get_filtered_works_async",
    "get_filtered_works_dict",
    "iter_filtered_works_async",
    "iter_filtered_works_cursor",
    "iter_filtered_works_offset",
    "metrics_collector",
    "pyalex_to_model",
]

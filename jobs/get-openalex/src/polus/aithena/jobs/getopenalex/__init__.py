"""getopenalex module for downloading OpenAlex records from their S3 bucket.

And interacting with their REST API.
"""

__version__ = "0.1.0-dev1"

# Re-export key functionality for easier imports
from polus.aithena.jobs.getopenalex.rest import APIError
from polus.aithena.jobs.getopenalex.rest import OpenAlexError  # Error handling
from polus.aithena.jobs.getopenalex.rest import PaginatorOptions
from polus.aithena.jobs.getopenalex.rest import RateLimitError
from polus.aithena.jobs.getopenalex.rest import WorksPaginator  # Pagination utilities
from polus.aithena.jobs.getopenalex.rest import api_session  # Context managers
from polus.aithena.jobs.getopenalex.rest import async_api_session
from polus.aithena.jobs.getopenalex.rest import (
    # Work retrieval functions
    get_filtered_works,
)
from polus.aithena.jobs.getopenalex.rest import get_filtered_works_async
from polus.aithena.jobs.getopenalex.rest import get_filtered_works_dict
from polus.aithena.jobs.getopenalex.rest import iter_filtered_works_async
from polus.aithena.jobs.getopenalex.rest import iter_filtered_works_cursor
from polus.aithena.jobs.getopenalex.rest import iter_filtered_works_offset
from polus.aithena.jobs.getopenalex.rest import metrics_collector  # Metrics collection
from polus.aithena.jobs.getopenalex.s3 import app as s3_app

# Import and export FastAPI application
try:
    from polus.aithena.jobs.getopenalex.api import api_app
except ImportError:
    # FastAPI might not be installed, in which case we set api_app to None
    api_app = None

__all__ = [
    "APIError",
    "OpenAlexError",
    "PaginatorOptions",
    "RateLimitError",
    "WorksPaginator",
    "api_app",
    "api_session",
    "async_api_session",
    "get_filtered_works",
    "get_filtered_works_async",
    "get_filtered_works_dict",
    "iter_filtered_works_async",
    "iter_filtered_works_cursor",
    "iter_filtered_works_offset",
    "metrics_collector",
    "s3_app",
]

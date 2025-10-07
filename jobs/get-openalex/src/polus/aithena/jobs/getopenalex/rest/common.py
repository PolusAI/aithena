"""Common utilities for the OpenAlex REST API."""

# Local imports
from polus.aithena.jobs.getopenalex.logger import get_logger
from polus.aithena.jobs.getopenalex.config import API_MAX_RETRIES
from polus.aithena.jobs.getopenalex.config import API_REQUEST_TIMEOUT

logger = get_logger(__name__)


class OpenAlexError(Exception):
    """Base exception for OpenAlex API errors."""

    pass


class RateLimitError(OpenAlexError):
    """Exception raised when hitting rate limits."""

    pass


class APIError(OpenAlexError):
    """Exception raised for API errors."""

    pass


# Constants
MAX_RETRIES = API_MAX_RETRIES
RATE_LIMIT_DELAY = 1  # second
logger.debug(f"API_REQUEST_TIMEOUT: {API_REQUEST_TIMEOUT}")  # Log config value
logger.debug(f"MAX_RETRIES: {MAX_RETRIES}")
logger.debug(f"RATE_LIMIT_DELAY: {RATE_LIMIT_DELAY}")

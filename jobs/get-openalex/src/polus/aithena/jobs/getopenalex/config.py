"""Configuration settings for the OpenAlex package.

This module centralizes all environment variable loading for consistent access
throughout the package.
"""

import os

from dotenv import find_dotenv
from dotenv import load_dotenv

from polus.aithena.jobs.getopenalex.logger import get_logger

logger = get_logger(__name__)

# Load environment variables from .env file if present
load_dotenv(find_dotenv(), override=True)

# =============================================
# S3 Operation Variables
# =============================================

# Determine if we should download from the last month automatically
S3_ALL_LAST_MONTH = os.getenv("ALL_LAST_MONTH", "False")
S3_ALL_LAST_MONTH = S3_ALL_LAST_MONTH in ["True", "true", "1"]

# Output directory for S3 downloads
S3_OUTPUT_PATH = os.getenv("S3_OUT_DIR", None)

# Starting date for S3 downloads
S3_FROM_DATE = os.getenv("S3_FROM_DATE", None)

# =============================================
# REST API Variables
# =============================================

# API host and port
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PYALEX_EMAIL = os.getenv("PYALEX_EMAIL", None)

# PostgreSQL connection string
POSTGRES_URL = os.getenv("POSTGRES_URL", None)

# Whether to use PostgreSQL for updates
USE_POSTGRES = os.getenv("USE_POSTGRES", "False")
USE_POSTGRES = USE_POSTGRES.lower() in ["true", "1", "yes", "y"]

# Job database URL for tracking update jobs
JOB_DATABASE_URL = os.getenv("JOB_DATABASE_URL", "sqlite:///./openalex_jobs.db")

# =============================================
# Update Job Configuration
# =============================================

# Number of records to process in a batch
UPDATE_BATCH_SIZE = int(os.getenv("UPDATE_BATCH_SIZE", "100"))

# Maximum number of records to process in a single job
UPDATE_MAX_RECORDS = int(os.getenv("UPDATE_MAX_RECORDS", "10000"))

# =============================================
# API Request Configuration
# =============================================

# OpenAlex API key (if available)
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", None)

# Default timeout for API requests in seconds
API_REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "30"))

# Maximum retries for API requests
API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))

logger.debug(
    f"""
             Initiliazed get-openalex config with:
             S3_ALL_LAST_MONTH={S3_ALL_LAST_MONTH},
             S3_OUTPUT_PATH={S3_OUTPUT_PATH},
             S3_FROM_DATE={S3_FROM_DATE},
             UPDATE_BATCH_SIZE={UPDATE_BATCH_SIZE},
             UPDATE_MAX_RECORDS={UPDATE_MAX_RECORDS},
             API_HOST={API_HOST},
             API_PORT={API_PORT},
             LOG_LEVEL={LOG_LEVEL},
             PYALEX_EMAIL={PYALEX_EMAIL},
             POSTGRES_URL={POSTGRES_URL},
             USE_POSTGRES={USE_POSTGRES},
             JOB_DATABASE_URL={JOB_DATABASE_URL},
             API_REQUEST_TIMEOUT={API_REQUEST_TIMEOUT},
             API_MAX_RETRIES={API_MAX_RETRIES}, OPENALEX_API_KEY={OPENALEX_API_KEY}"""
)

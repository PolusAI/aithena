"""This module contains the global configuration that are inherited by any child package."""
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from first .env file found in a parent hierarchy
load_dotenv(find_dotenv(), override=True)

# log level for the whole application
os.environ.setdefault("AITHENA_LOG_LEVEL", "DEBUG")
AITHENA_LOG_LEVEL = os.environ.get("AITHENA_LOG_LEVEL")

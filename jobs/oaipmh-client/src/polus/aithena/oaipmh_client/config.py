import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

TIMEOUT = int(os.environ.get("TIMEOUT") or "30")
RETRY_AFTER = int(os.environ.get("RETRY_AFTER") or "5")
RETRY_ATTEMPTS = int(os.environ.get("RETRY_ATTEMPTS") or "3")


import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

# automatically let python do from whatever day is today
ALL_LAST_MONTH = os.getenv("ALL_LAST_MONTH", "False")
ALL_LAST_MONTH = ALL_LAST_MONTH in ["True", "true", "1"]

OUTPUT_PATH = os.getenv("OUT_DIR", None)

FROM_DATE = os.getenv("FROM_DATE", None)

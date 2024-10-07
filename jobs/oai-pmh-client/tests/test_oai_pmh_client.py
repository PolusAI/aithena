"""Test the OaiPmhClient."""

import datetime
import os
from pathlib import Path
import shutil
import tempfile
from dotenv import find_dotenv
from dotenv import load_dotenv
from polus.aithena.oaipmh_client.oai_pmh_client import OaiPmhClient
from polus.aithena.oaipmh_client.oai_pmh_types import XmlDate
from tenacity import retry, stop_after_attempt, wait_fixed

tmpdirname = tempfile.mkdtemp()
load_dotenv(find_dotenv(), override=True)
out_dir = Path(os.environ.get("TEST_TEMP_DIR", tmpdirname))


@retry(stop=stop_after_attempt(3), wait=wait_fixed(30))
def test_oai_pmh_client() -> None:
    """Test the OaiPmhClient."""
    arxiv_client = OaiPmhClient("https://export.arxiv.org/oai2", out_dir=out_dir)

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    from_ = XmlDate.from_datetime(yesterday)
    arxiv_client.list_records("arXiv", from_=from_)

    # delete temp directory
    shutil.rmtree(tmpdirname)

"""Test the OaiPmhClient."""

import datetime
import os
from pathlib import Path

from dotenv import find_dotenv
from dotenv import load_dotenv
from polus.aithena.document_services.arxiv_abstract_ingestion import config
from polus.aithena.document_services.arxiv_abstract_ingestion.embed_abstracts_nvembed import (
    embed_abstracts_nvembed,
)

load_dotenv(find_dotenv(), override=True)
out_dir = Path(os.environ.get("DATA_DIR", "."))


# TODO add dummy data for tests.
def test_arxiv_abstract_ingestion_date() -> None:
    """Test the OaiPmhClient."""
    embed_abstracts_nvembed(date=datetime.datetime(2024, 9, 5))


def test_arxiv_abstract_ingestion_inp_dir() -> None:
    """Test the OaiPmhClient."""
    inp_dir = config.ARXIV_LIST_RECORDS_DIR / "2024-09-05" / "arXiv"
    embed_abstracts_nvembed(inp_dir=inp_dir)

"""Download data for arxiv.

The only information needed is the date of the first published document to retrieve.
All documents published after this date will be retrieved.

NOTE : we could have an 'until' to bound the search but
it is discouraged in the arxiv doc
so it is not currently implemented
see [arxiv guidelines](https://info.arxiv.org/help/oa/index.html).
"""

import datetime
import os
from pathlib import Path

from dotenv import find_dotenv
from dotenv import load_dotenv
from polus.aithena.oaipmh_client.oai_pmh_client import OaiPmhClient
from polus.aithena.oaipmh_client.oai_pmh_types import XmlDate

load_dotenv(find_dotenv(), override=True)
out_dir = Path(os.environ.get("TEST_TEMP_DIR", "."))
arxiv_client = OaiPmhClient("https://export.arxiv.org/oai2", out_dir=out_dir)

date = datetime.datetime.now()
date = date - datetime.timedelta(days=1)
from_ = XmlDate.from_datetime(date)
arxiv_client.list_records("arXiv", from_=from_)

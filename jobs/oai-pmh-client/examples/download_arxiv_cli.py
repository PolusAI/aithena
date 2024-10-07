"""Example script to download metadata from arXiv using the CLI."""

import datetime
import os
from pathlib import Path

from dotenv import find_dotenv
from dotenv import load_dotenv
from polus.aithena.oaipmh_client.__main__ import app
from typer.testing import CliRunner

load_dotenv(find_dotenv(), override=True)

runner = CliRunner()

url = "https://export.arxiv.org/oai2"
date = datetime.datetime.now()
date = date - datetime.timedelta(days=1)
from_ = date
format_ = "oai_dc"
out_dir = Path(os.environ.get("TEST_TEMP_DIR", ".")).resolve()

result = runner.invoke(
    app,
    [
        "--url",
        url,
        "--from",
        from_,
        "--format",
        format_,
        "--outDir",
        out_dir,
    ],
    catch_exceptions=True,
)

"""Test the command line interface."""

import datetime
import os
from pathlib import Path
import shutil
import tempfile

from dotenv import find_dotenv
from dotenv import load_dotenv
from polus.aithena.oaipmh_client.__main__ import app
from tenacity import retry, stop_after_attempt, wait_fixed
from typer.testing import CliRunner

tmpdirname = tempfile.mkdtemp()
load_dotenv(find_dotenv(), override=True)
out_dir = Path(os.environ.get("TEST_TEMP_DIR", tmpdirname))

runner = CliRunner()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(30))
def test_cli() -> None:
    """Test the command line."""
    url = "https://export.arxiv.org/oai2"
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    from_ = yesterday
    format_ = "arXiv"

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

    print(result.exception)  # noqa:T201
    print(result.exc_info)  # noqa:T201
    print(result.exc_info[2])  # noqa:T201

    assert result.exit_code == 0

    # delete temp directory
    shutil.rmtree(tmpdirname)

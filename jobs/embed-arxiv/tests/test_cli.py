"""Test the command line interface."""

import datetime

from dotenv import find_dotenv
from dotenv import load_dotenv
from polus.aithena.document_services.arxiv_abstract_ingestion import config
from polus.aithena.document_services.arxiv_abstract_ingestion.__main__ import app
from typer.testing import CliRunner

load_dotenv(find_dotenv(), override=True)

runner = CliRunner()


def test_cli_date() -> None:
    """Test the command line."""
    date = datetime.datetime(2024, 9, 5)

    result = runner.invoke(
        app,
        [
            "--date",
            date,
        ],
        catch_exceptions=True,
    )

    print(result.exception)  # noqa:T201
    print(result.exc_info)  # noqa:T201
    print(result.exc_info[2])  # noqa:T201

    assert result.exit_code == 0


def test_cli_inp_dir():
    inp_dir = config.ARXIV_LIST_RECORDS_DIR / "2024-09-05" / "arXiv"

    result = runner.invoke(
        app,
        [
            "--inpDir",
            inp_dir,
        ],
        catch_exceptions=True,
    )

    assert result.exit_code == 0

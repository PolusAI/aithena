"""Example script that show how to embed arxiv abstracts and daving to db using the CLI.

It expects the ollama server to be running.

At a minimum, the following environment variables must be defined:
DATA_DIR
EMBED_URL
"""

from dotenv import find_dotenv
from dotenv import load_dotenv
from polus.aithena.document_services.arxiv_abstract_ingestion import config
from polus.aithena.document_services.arxiv_abstract_ingestion.__main__ import app
from typer.testing import CliRunner

load_dotenv(find_dotenv())

runner = CliRunner()

inp_dir = config.ARXIV_LIST_RECORDS_DIR / "2024-09-05" / "arXiv"

result = runner.invoke(
    app,
    [
        "--inpDir",
        inp_dir,
    ],
    catch_exceptions=True,
)

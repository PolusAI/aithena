"""OAI PMH client cli."""
import datetime
from pathlib import Path

import typer
from polus.aithena.common.logger import get_logger

from . import oai_pmh_types as oai
from .oai_pmh_client import OaiPmhClient

logger = get_logger(__file__)

app = typer.Typer()


@app.command()
def main(
    url: str = typer.Option(
        "https://export.arxiv.org/oai2",
        "--url",
        help="service url",
    ),
    from_: datetime.datetime = typer.Option(
        datetime.datetime.now(),
        "--from",
        help="from",
    ),
    format_: str = typer.Option("oai_dc", "--format", help="metadata format"),
    out_dir: Path = typer.Option(
        ...,
        "--outDir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        help="Output directory",
    ),
) -> None:
    """OAI PMH client cli."""
    logger.info(f"url = {url}")
    logger.info(f"outDir = {out_dir}")
    logger.info(f"from = {from_}")
    logger.info(f"format = {format_}")

    client = OaiPmhClient(url, out_dir=out_dir)
    date = oai.XmlDate.from_datetime(from_)
    client.list_records(metadata_prefix=format_, from_=date)


if __name__ == "__main__":
    app()

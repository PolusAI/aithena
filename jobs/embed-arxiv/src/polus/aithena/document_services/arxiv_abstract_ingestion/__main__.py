"""OAI PMH client cli."""
import datetime
from pathlib import Path

# from polus.aithena.document_services.arxiv_abstract_ingestion.embed_abstracts_instructorxl import (
#     embed_abstracts_instructorxl,
# )
from polus.aithena.document_services.arxiv_abstract_ingestion.embed_abstracts_aithena_services import (  # noqa
    embed_abstracts_aithena_services,
)
import typer
from polus.aithena.common.logger import get_logger

logger = get_logger(__file__)

app = typer.Typer()


@app.command()
def main(
    inp_dir: Path
    | None = typer.Option(
        None,
        "--inpDir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Input directory",
    ),
    date_: datetime.datetime = typer.Option(
        datetime.datetime.now(),
        "--date",
        help="Select directory based on date",
    ),
) -> None:
    """Arxiv Abstract Ingestion Cli."""
    logger.info(f"inpDir = {inp_dir}")
    if inp_dir is not None:
        logger.info(
            "input directory provided. If provided date parameter will be ignored."
        )
        embed_abstracts_aithena_services(inp_dir=inp_dir)
    else:
        logger.info("input directory not provided. Using date parameter.")
        embed_abstracts_aithena_services(date=date_)


if __name__ == "__main__":
    app()

# mypy: disable-error-code="import-untyped"
"""Get OpenAlex from S3 Bucket."""
# pylint: disable=W1203, E0401, E0611
from datetime import date
from pathlib import Path

import typer
from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import init_dir
from polus.aithena.jobs.getopenalex.config import FROM_DATE, ALL_LAST_MONTH, OUTPUT_PATH
from polus.aithena.jobs.getopenalex.s3_types import SnapshotS3

app = typer.Typer()

if OUTPUT_PATH is not None:
    OUTPUT_PATH = init_dir(Path(OUTPUT_PATH))


@app.command()
def main(
    out_dir: Path | None = typer.Option(
        OUTPUT_PATH,
        "--outDir",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Output directory",
    ),
    from_date: str | None = typer.Option(
        FROM_DATE,
        "--fromDate",
        help="Download from this date (inclusive)",
    ),
    only_type: str | None = typer.Option(
        None,
        "--onlyType",
        help="Download only this type of data",
    ),
) -> None:
    """Get OpenAlex from S3 Bucket."""
    logger = get_logger(__file__)
    logger.info(f"outDir = {out_dir}")
    if ALL_LAST_MONTH:
        today_ = date.today()
        from_date = today_.replace(day=1, month=today_.month-1).isoformat()
    logger.info(f"fromDate = {from_date}")
    if only_type is not None:
        only_type = only_type.lower()
        logger.info(f"onlyType = {only_type}")
    else:
        logger.info("Downloading all types")

    snapshot = SnapshotS3()
    if only_type is not None:
        snapshot.download_all_of_type(
            type_=only_type, output_path=out_dir, from_date=from_date)
    else:
        snapshot.download_all(from_date=from_date, output_path=out_dir)


if __name__ == "__main__":
    main()

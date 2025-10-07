# mypy: disable-error-code="import-untyped"
"""S3 interface for downloading OpenAlex snapshots."""
# pylint: disable=W1203, E0401, E0611
from datetime import date
from pathlib import Path

import typer

from polus.aithena.jobs.getopenalex.logger import get_logger
from polus.aithena.jobs.getopenalex.utils import init_dir
from polus.aithena.jobs.getopenalex.config import S3_ALL_LAST_MONTH
from polus.aithena.jobs.getopenalex.config import S3_FROM_DATE
from polus.aithena.jobs.getopenalex.config import S3_OUTPUT_PATH
from polus.aithena.jobs.getopenalex.s3.s3_types import TYPES
from polus.aithena.jobs.getopenalex.s3.s3_types import SnapshotS3

app = typer.Typer()

if S3_OUTPUT_PATH is not None:
    S3_OUTPUT_PATH = init_dir(Path(S3_OUTPUT_PATH))


@app.command()
def download(
    out_dir: Path | None = typer.Option(
        S3_OUTPUT_PATH,
        "--outDir",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Output directory",
    ),
    from_date: str | None = typer.Option(
        S3_FROM_DATE,
        "--fromDate",
        help="Download from this date (inclusive)",
    ),
    only_type: str | None = typer.Option(
        None,
        "--onlyType",
        help="Download only this type of data",
    ),
) -> None:
    """Download OpenAlex snapshots from S3 Bucket."""
    logger = get_logger(__file__)
    logger.info(f"outDir = {out_dir}")
    if S3_ALL_LAST_MONTH:
        today_ = date.today()
        from_date = today_.replace(day=1, month=today_.month - 1).isoformat()
    logger.info(f"fromDate = {from_date}")
    if only_type is not None:
        only_type = only_type.lower()
        if only_type not in TYPES:
            valid_types = ", ".join(TYPES)
            logger.error(f"Invalid type: {only_type}. Valid types are: {valid_types}")
            raise ValueError(
                f"Invalid type: {only_type}. Valid types are: {valid_types}",
            )
        logger.info(f"onlyType = {only_type}")
    else:
        logger.info("Downloading all types")

    snapshot = SnapshotS3()
    if only_type is not None:
        snapshot.download_all_of_type(
            type_=only_type,
            output_path=out_dir,
            from_date=from_date,
        )
    else:
        snapshot.download_all(from_date=from_date, output_path=out_dir)


@app.command()
def list_available(
    type_: str | None = typer.Option(
        None,
        "--type",
        help="List only this type of data",
    ),
    from_date: str | None = typer.Option(
        S3_FROM_DATE,
        "--fromDate",
        help="List from this date (inclusive)",
    ),
) -> None:
    """List available OpenAlex snapshots in S3 Bucket."""
    logger = get_logger(__file__)

    if S3_ALL_LAST_MONTH:
        today_ = date.today()
        from_date = today_.replace(day=1, month=today_.month - 1).isoformat()
    logger.info(f"fromDate = {from_date}")

    snapshot = SnapshotS3()

    if type_ is not None:
        type_ = type_.lower()
        if type_ not in TYPES:
            valid_types = ", ".join(TYPES)
            logger.error(f"Invalid type: {type_}. Valid types are: {valid_types}")
            raise ValueError(f"Invalid type: {type_}. Valid types are: {valid_types}")

        dirs = snapshot.ls_dirs(type_, from_date=from_date)
        logger.info(f"Available {type_} snapshots from {from_date}:")
        for dir_ in dirs:
            logger.info(f"{dir_.type} - {dir_.date}")
    else:
        dirs_dict = snapshot.ls_dirs_dict(from_date=from_date)
        logger.info(f"Available snapshots from {from_date}:")
        for type_, dirs_list in dirs_dict.items():  # Use dirs_list for clarity
            logger.info(f"\n{type_} snapshots:")
            for dir_ in dirs_list:
                logger.info(f"  {dir_.date}")


if __name__ == "__main__":
    app()

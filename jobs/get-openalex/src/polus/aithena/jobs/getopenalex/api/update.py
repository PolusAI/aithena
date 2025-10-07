"""OpenAlex database update jobs.

This module provides functionality to sync a PostgreSQL database with
data from the OpenAlex API. It includes incremental updates based on modification date.
"""

from collections.abc import Iterator
from datetime import datetime
from datetime import timedelta
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import col
from sqlmodel import create_engine
from sqlmodel import select

from polus.aithena.jobs.getopenalex.logger import get_logger
from polus.aithena.jobs.getopenalex import iter_filtered_works_cursor
from polus.aithena.jobs.getopenalex.api.database import Database
from polus.aithena.jobs.getopenalex.api.database import Job
from polus.aithena.jobs.getopenalex.api.database import JobRepository
from polus.aithena.jobs.getopenalex.api.database import JobStatus
from polus.aithena.jobs.getopenalex.api.database import JobType
from polus.aithena.jobs.getopenalex.api.logging_helpers import JobLogger
from polus.aithena.jobs.getopenalex.config import POSTGRES_URL
from polus.aithena.jobs.getopenalex.config import UPDATE_BATCH_SIZE
from polus.aithena.jobs.getopenalex.config import UPDATE_MAX_RECORDS
from polus.aithena.jobs.getopenalex.config import USE_POSTGRES

logger = get_logger(__name__)

# Default PostgreSQL connection string - should be overridden by environment variables
DEFAULT_POSTGRES_URL = "postgresql://postgres:postgres@localhost:5432/openalex"

# Default values
DEFAULT_BATCH_SIZE = 100
DEFAULT_MAX_RECORDS = 10000


class WorkRecord(BaseModel):
    """Simplified OpenAlex work record for database operations."""

    id: str
    title: str
    publication_date: str | None = None
    doi: str | None = None
    updated_date: str | None = None

    @classmethod
    def from_openalex(cls, work_data: dict[str, Any]) -> "WorkRecord":
        """Create a WorkRecord from OpenAlex API data."""
        return cls(
            id=work_data.get("id", ""),
            title=work_data.get("title", ""),
            publication_date=work_data.get("publication_date"),
            doi=work_data.get("doi"),
            updated_date=work_data.get("updated_date"),
        )


class OpenAlexDBUpdater:
    """Update a PostgreSQL database with data from OpenAlex API."""

    def __init__(
        self,
        postgres_url: str | None = None,
        job_db: Database | None = None,
        batch_size: int | None = None,
        max_records: int | None = None,
        use_postgres: bool | None = None,
    ) -> None:
        """Initialize the database updater."""
        # PostgreSQL connection
        self.postgres_url = postgres_url or POSTGRES_URL or DEFAULT_POSTGRES_URL

        # Whether to use PostgreSQL for updates
        self.use_postgres = use_postgres if use_postgres is not None else USE_POSTGRES

        # Initialize PostgreSQL engine if enabled
        self.pg_engine = None
        if self.use_postgres:
            if not self.postgres_url:
                logger.warning(
                    "PostgreSQL URL is not set, disabling PostgreSQL updates",
                )
                self.use_postgres = False
            else:
                try:
                    self.pg_engine = create_engine(self.postgres_url, echo=False)
                    logger.info(
                        f"PostgreSQL connection established at {self.postgres_url}",
                    )
                except SQLAlchemyError as e:
                    logger.error(f"Failed to connect to PostgreSQL: {e!s}")
                    self.use_postgres = False
        else:
            logger.info("PostgreSQL updates are disabled")

        # Job database
        self.job_db = job_db or Database()
        self.job_repo = JobRepository(self.job_db)

        # Configuration
        self.batch_size = batch_size or UPDATE_BATCH_SIZE or DEFAULT_BATCH_SIZE
        self.max_records = max_records or UPDATE_MAX_RECORDS or DEFAULT_MAX_RECORDS

        # Ensure tables exist
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure required tables exist in both databases."""
        # Job database tables
        self.job_db.create_tables()

        # PostgreSQL tables - create if they don't exist and PostgreSQL is enabled
        if self.use_postgres and self.pg_engine:
            # Define models for the PostgreSQL database tables
            class Work(SQLModel, table=True):
                __tablename__ = "openalex_works"

                id: str = Field(primary_key=True)
                title: str
                publication_date: str | None = Field(default=None, index=True)
                doi: str | None = Field(default=None, index=True)
                updated_date: str | None = Field(default=None, index=True)
                data: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
                last_updated: datetime = Field(default_factory=datetime.now)

            # Create tables if they don't exist
            try:
                SQLModel.metadata.create_all(self.pg_engine)
                logger.info("PostgreSQL tables created or already exist")
            except SQLAlchemyError as e:
                logger.error(f"Failed to create PostgreSQL tables: {e!s}")
                self.use_postgres = False

    def _get_last_update_date(self) -> str | None:
        """Get the last update date from the job history."""
        last_job = self.job_repo.get_last_successful_job(JobType.WORKS_UPDATE)
        if last_job and last_job.parameters.get("from_date"):
            return last_job.parameters["from_date"]

        # Default to 7 days ago if no previous job
        return (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    def _process_works_loop(
        self,
        from_date: str,
        logger: JobLogger,
    ) -> tuple[int, int, int, int]:
        """Iterate through works and process them."""
        processed = 0
        created = 0
        updated = 0
        failed = 0

        logger.info(f"Starting works update from {from_date}", from_date=from_date)
        if not self.use_postgres:
            logger.info(
                "PostgreSQL updates are disabled, "
                "job will only process and count records",
            )

        for work in self._iterate_works(from_date=from_date, logger=logger):
            try:
                if self.use_postgres:
                    result = self._process_work(work)
                    processed += 1
                    if result == "created":
                        created += 1
                    elif result == "updated":
                        updated += 1
                else:
                    processed += 1
                    created += 1  # Mark all as "new" for counting

                if processed % 100 == 0:
                    logger.progress(
                        current=processed,
                        created=created,
                        updated=updated,
                        failed=failed,
                    )

                if processed >= self.max_records:
                    logger.info(f"Reached maximum records limit ({self.max_records})")
                    break

            except Exception as e:  # noqa: BLE001
                failed += 1
                error_message = f"Error processing work: {e!s}"
                work_id = work.get("id", "unknown")
                logger.error(error_message, work_id=work_id)

        return processed, created, updated, failed

    def update_works(
        self,
        from_date: str | None = None,
        job_id: int | None = None,
    ) -> Job:
        """Update works in the database from the OpenAlex API.

        Args:
            from_date: ISO format date string (YYYY-MM-DD) to start updates from
            job_id: Optional existing job ID to use

        Returns:
            The completed job record
        """
        # Determine from_date if not provided
        if not from_date:
            from_date = self._get_last_update_date()

        # Create or get job
        if job_id:
            job = self.job_repo.get_job(job_id)
            if not job:
                raise ValueError(f"Job with ID {job_id} not found")
        else:
            job = self.job_repo.create_job(
                job_type=JobType.WORKS_UPDATE,
                parameters={"from_date": from_date},
            )

        # Logger
        logger = JobLogger(f"works_update_{job.id}")

        try:
            # Start job
            job = self.job_repo.start_job(job.id)
            logger.start_job(from_date=from_date)

            # Process works
            processed, created, updated, failed = self._process_works_loop(
                from_date,
                logger,
            )

            # Log completion summary
            status = JobStatus.COMPLETED
            if self.use_postgres:
                logger.info(
                    f"Works update completed: {processed} processed, "
                    f"{created} created, "
                    f"{updated} updated, {failed} failed",
                    processed=processed,
                    created=created,
                    updated=updated,
                    failed=failed,
                )
            else:
                logger.info(
                    f"Works counting completed (PostgreSQL disabled): "
                    f"{processed} processed, "
                    f"{failed} failed",
                    processed=processed,
                    failed=failed,
                )

        except Exception as e:  # noqa: BLE001
            # Handle job failure
            status = JobStatus.FAILED
            error_message = str(e)
            logger.error(f"Works update failed: {error_message}")

            # Complete the job with failure status
            return self.job_repo.complete_job(
                job_id=job.id,
                status=status,
                records_processed=processed if "processed" in locals() else 0,
                records_created=created if "created" in locals() else 0,
                records_updated=updated if "updated" in locals() else 0,
                records_failed=failed if "failed" in locals() else 0,
                error_message=error_message,
            )

        # Complete the job with success status
        logger.end_job(status="success")
        return self.job_repo.complete_job(
            job_id=job.id,
            status=status,
            records_processed=processed,
            records_created=created,
            records_updated=updated,
            records_failed=failed,
        )

    def _iterate_works(
        self,
        from_date: str,
        logger: JobLogger,
    ) -> Iterator[dict[str, Any]]:
        """Iterate through works from OpenAlex API.

        Args:
            from_date: From date in ISO format
            logger: JobLogger instance for logging

        Yields:
            Work dictionaries from the API
        """
        # Define filters
        filters = {
            "from_updated_date": from_date,
        }

        logger.info("Starting iteration through works", filters=filters)

        # Use cursor-based pagination for efficiency
        for i, work in enumerate(iter_filtered_works_cursor(filters=filters)):
            # Convert to dict for processing
            yield work.model_dump()

            # Periodically log progress
            if i > 0 and i % 1000 == 0:
                logger.info(f"Iterated through {i} works so far")

    def _process_work(self, work_data: dict[str, Any]) -> str:
        """Process a single work record.

        Args:
            work_data: Work data from OpenAlex API

        Returns:
            String indicating operation: 'created', 'updated', or 'skipped'
        """
        # Skip if PostgreSQL is disabled
        if not self.use_postgres or not self.pg_engine:
            return "skipped"

        # Convert to a simplified record
        work_record = WorkRecord.from_openalex(work_data)

        # Check if work exists in database
        with Session(self.pg_engine) as session:
            # Check if work exists
            stmt = (
                select(SQLModel)
                .where(col("id") == work_record.id)
                .select_from(SQLModel.metadata.tables["openalex_works"])
            )
            existing_work = session.exec(stmt).first()

            if existing_work:
                # Update existing work
                for field, value in work_record.model_dump().items():
                    setattr(existing_work, field, value)

                # Update full data JSON and timestamp
                existing_work.data = work_data
                existing_work.last_updated = datetime.now()

                session.add(existing_work)
                session.commit()
                return "updated"
            # Create new work
            # Need to use raw SQL to insert due to dynamic table
            from sqlalchemy import insert

            stmt = insert(SQLModel.metadata.tables["openalex_works"]).values(
                id=work_record.id,
                title=work_record.title,
                publication_date=work_record.publication_date,
                doi=work_record.doi,
                updated_date=work_record.updated_date,
                data=work_data,
                last_updated=datetime.now(),
            )
            session.execute(stmt)
            session.commit()
            return "created"


# Convenience function to run an update job
def run_works_update(
    from_date: str | None = None,
    postgres_url: str | None = None,
    job_db_url: str | None = None,
    batch_size: int | None = None,
    max_records: int | None = None,
    use_postgres: bool | None = None,
) -> Job:
    """Run a works update job.

    Args:
        from_date: ISO format date string (YYYY-MM-DD) to start updates from
        postgres_url: PostgreSQL connection URL
        job_db_url: Job database connection URL
        batch_size: Number of records to process in a batch
        max_records: Maximum number of records to process
        use_postgres: Whether to use PostgreSQL for updates (overrides config)

    Returns:
        The completed job record
    """
    # Setup job database
    job_db = Database(job_db_url) if job_db_url else None

    # Create updater
    updater = OpenAlexDBUpdater(
        postgres_url=postgres_url,
        job_db=job_db,
        batch_size=batch_size,
        max_records=max_records,
        use_postgres=use_postgres,
    )

    # Run update
    return updater.update_works(from_date=from_date)

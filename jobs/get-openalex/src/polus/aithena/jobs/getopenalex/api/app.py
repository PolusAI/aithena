"""FastAPI application for OpenAlex REST API operations."""

import contextlib
from datetime import datetime
from typing import Any

from fastapi import BackgroundTasks
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.exc import SQLAlchemyError

from polus.aithena.jobs.getopenalex.logger import get_logger
from polus.aithena.jobs.getopenalex import APIError
from polus.aithena.jobs.getopenalex import OpenAlexError
from polus.aithena.jobs.getopenalex import RateLimitError
from polus.aithena.jobs.getopenalex import WorksPaginator
from polus.aithena.jobs.getopenalex import get_filtered_works_async
from polus.aithena.jobs.getopenalex.api.database import Job as DBJob
from polus.aithena.jobs.getopenalex.api.database import JobStatus
from polus.aithena.jobs.getopenalex.api.database import JobType
from polus.aithena.jobs.getopenalex.api.database_manager import db_manager
from polus.aithena.jobs.getopenalex.api.update import run_works_update
from polus.aithena.jobs.getopenalex.config import USE_POSTGRES

logger = get_logger(__name__)

app = FastAPI(
    title="OpenAlex API",
    description="API for querying OpenAlex academic data and managing database updates",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on server startup."""
    logger.info("Starting FastAPI server, initializing database...")
    db_manager.initialize()
    logger.info("Database initialization complete")


# Models
class WorkSearchParams(BaseModel):
    """Parameters for searching works."""

    query: str | None = Field(None, description="Search query")
    from_date: str | None = Field(
        None,
        description="From publication date (YYYY-MM-DD)",
    )
    to_date: str | None = Field(None, description="To publication date (YYYY-MM-DD)")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    page: int = Field(1, description="Page number", ge=1)
    per_page: int = Field(10, description="Results per page", ge=1, le=100)
    author_id: str | None = Field(None, description="Filter by author ID")
    institution_id: str | None = Field(None, description="Filter by institution ID")
    venue_id: str | None = Field(None, description="Filter by venue ID")
    concept_id: str | None = Field(None, description="Filter by concept ID")
    doi: str | None = Field(None, description="Filter by DOI")
    pmcid: str | None = Field(
        None,
        description="Filter by PubMed Central ID (pmcid)",
    )
    pmid: str | None = Field(None, description="Filter by PubMed ID (pmid)")
    raw: bool = Field(
        False, description="Return raw PyalexWork data instead of Work model"
    )

    def to_filters(self) -> dict[str, Any]:
        """Convert search parameters to OpenAlex API filters."""
        filters: dict[str, Any] = {}

        if self.from_date:
            filters["from_publication_date"] = self.from_date
        if self.to_date:
            filters["to_publication_date"] = self.to_date
        if self.author_id:
            filters["author.id"] = self.author_id
        if self.institution_id:
            filters["institutions.id"] = self.institution_id
        if self.venue_id:
            filters["host_venue.id"] = self.venue_id
        if self.concept_id:
            filters["concepts.id"] = self.concept_id
        if self.doi:
            filters["doi"] = self.doi
        if self.pmid:
            filters["pmid"] = self.pmid
        if self.pmcid:
            filters["pmcid"] = self.pmcid

        return filters


class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""

    count: int
    next_page: int | None = None
    prev_page: int | None = None
    current_page: int
    total_pages: int | None = None
    results: list[dict[str, Any]]


class Job(BaseModel):
    """Job model for API responses."""

    id: int
    job_type: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    parameters: dict[str, Any] = {}
    error_message: str | None = None
    duration_seconds: float | None = None

    @classmethod
    def from_db_job(cls, db_job: DBJob) -> "Job":
        """Convert a database job to an API job."""
        return cls(
            id=db_job.id,
            job_type=db_job.job_type.value,
            status=db_job.status.value,
            created_at=db_job.created_at,
            started_at=db_job.started_at,
            completed_at=db_job.completed_at,
            records_processed=db_job.records_processed,
            records_created=db_job.records_created,
            records_updated=db_job.records_updated,
            records_failed=db_job.records_failed,
            parameters=db_job.parameters,
            error_message=db_job.error_message,
            duration_seconds=db_job.duration_seconds,
        )


class UpdateRequest(BaseModel):
    """Request to start a data update job."""

    job_type: str = Field(..., description="Type of update job")
    from_date: str | None = Field(
        None,
        description="Start date for updates (YYYY-MM-DD)",
    )
    max_records: int | None = Field(None, description="Maximum records to process")
    use_postgres: bool | None = Field(
        None,
        description="Whether to store data in PostgreSQL",
    )


class JobLogEntry(BaseModel):
    """Job log entry for API responses."""

    id: int
    job_id: int
    timestamp: datetime
    level: str
    message: str
    details: dict[str, Any] = {}


# Routes
@app.get("/")
async def root() -> dict:
    """API root endpoint."""
    return {
        "name": "OpenAlex API",
        "version": "0.1.0",
        "description": (
            "API for querying OpenAlex academic data and managing database updates"
        ),
        "endpoints": [
            "/works",
            "/works/search",
            "/works/{work_id}",
            "/health",
            "/jobs",
            "/jobs/{job_id}",
            "/jobs/{job_id}/logs",
            "/update",
            "/docs",
        ],
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/works", response_model=PaginatedResponse)
async def get_works(
    query: str | None = Query(None, description="Search query"),
    from_date: str | None = Query(
        None,
        description="From publication date (YYYY-MM-DD)",
    ),
    to_date: str | None = Query(
        None,
        description="To publication date (YYYY-MM-DD)",
    ),
    author_id: str | None = Query(None, description="Filter by author ID"),
    institution_id: str | None = Query(None, description="Filter by institution ID"),
    venue_id: str | None = Query(None, description="Filter by venue ID"),
    concept_id: str | None = Query(None, description="Filter by concept ID"),
    doi: str | None = Query(None, description="Filter by DOI"),
    pmcid: str | None = Query(
        None,
        description="Filter by PubMed Central ID (pmcid)",
    ),
    pmid: str | None = Query(None, description="Filter by PubMed ID (pmid)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    raw: bool = Query(
        False, description="Return raw PyalexWork data instead of Work model"
    ),
) -> PaginatedResponse:
    """Get works from OpenAlex with various filters."""
    search_params = WorkSearchParams(
        query=query,
        from_date=from_date,
        to_date=to_date,
        author_id=author_id,
        institution_id=institution_id,
        venue_id=venue_id,
        concept_id=concept_id,
        doi=doi,
        pmcid=pmcid,
        pmid=pmid,
        page=page,
        per_page=per_page,
        limit=limit,
        raw=raw,
    )

    filters = search_params.to_filters()
    logger.info(f"Searching works with query='{query}' and filters={filters}")

    try:
        paginator = WorksPaginator(
            search=query,
            filters=filters,
            per_page=per_page,
            initial_page=page,
            raw=raw,
        )

        results_page = await paginator.get_page_async()
        results = [
            work.model_dump() if not raw and hasattr(work, "model_dump") else work
            for work in results_page
        ]

        return PaginatedResponse(
            count=paginator.count if paginator.count else len(results),
            current_page=paginator.current_page,
            next_page=paginator.current_page + 1 if paginator.has_next else None,
            prev_page=(
                paginator.current_page - 1 if paginator.current_page > 1 else None
            ),
            total_pages=paginator.total_pages,
            results=results[:limit],  # Apply limit
        )

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e!s}")
        raise HTTPException(
            status_code=429,
            detail="OpenAlex rate limit exceeded",
        ) from e
    except APIError as e:
        logger.error(f"API error: {e!s}")
        raise HTTPException(
            status_code=502,
            detail=f"OpenAlex API error: {e!s}",
        ) from e
    except OpenAlexError as e:
        logger.error(f"OpenAlex error: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"OpenAlex error: {e!s}",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error: {e!s}")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error occurred",
        ) from e


@app.post("/works/search", response_model=PaginatedResponse)
async def search_works(search_params: WorkSearchParams) -> PaginatedResponse:
    """Search for works with a request body."""
    filters = search_params.to_filters()
    logger.info(
        f"Searching works with query='{search_params.query}' and filters={filters}",
    )

    try:
        paginator = WorksPaginator(
            search=search_params.query,
            filters=filters,
            per_page=search_params.per_page,
            initial_page=search_params.page,
            raw=search_params.raw,
        )

        results_page = await paginator.get_page_async()
        results = [
            (
                work.model_dump()
                if not search_params.raw and hasattr(work, "model_dump")
                else work
            )
            for work in results_page
        ]

        return PaginatedResponse(
            count=paginator.count if paginator.count else len(results),
            current_page=paginator.current_page,
            next_page=paginator.current_page + 1 if paginator.has_next else None,
            prev_page=(
                paginator.current_page - 1 if paginator.current_page > 1 else None
            ),
            total_pages=paginator.total_pages,
            results=results[: search_params.limit],  # Apply limit
        )

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e!s}")
        raise HTTPException(
            status_code=429,
            detail="OpenAlex rate limit exceeded",
        ) from e
    except APIError as e:
        logger.error(f"API error: {e!s}")
        raise HTTPException(
            status_code=502,
            detail=f"OpenAlex API error: {e!s}",
        ) from e
    except OpenAlexError as e:
        logger.error(f"OpenAlex error: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"OpenAlex error: {e!s}",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error: {e!s}")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error occurred",
        ) from e


@app.get("/works/{work_id}")
async def get_work_by_id(work_id: str) -> dict:
    """Get a specific work by ID."""
    try:
        # Format the work ID if needed (e.g., adding prefix)
        if not work_id.startswith("https://openalex.org/"):
            formatted_id = f"https://openalex.org/{work_id}"
        else:
            formatted_id = work_id

        works = await get_filtered_works_async(
            filters={"id": formatted_id},
            max_results=1,
        )

        if not works:
            raise HTTPException(
                status_code=404,
                detail=f"Work with ID {work_id} not found",
            )

        return works[0].model_dump()

    except HTTPException:
        raise
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e!s}")
        raise HTTPException(
            status_code=429,
            detail="OpenAlex rate limit exceeded",
        ) from e
    except APIError as e:
        logger.error(f"API error: {e!s}")
        raise HTTPException(
            status_code=502,
            detail=f"OpenAlex API error: {e!s}",
        ) from e
    except OpenAlexError as e:
        logger.error(f"OpenAlex error: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"OpenAlex error: {e!s}",
        ) from e
    except Exception as e:
        logger.exception(f"Unexpected error: {e!s}")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error occurred",
        ) from e


# Job management endpoints
@app.get("/jobs", response_model=list[Job])
async def get_jobs(
    status: str | None = Query(None, description="Filter by job status"),
    job_type: str | None = Query(None, description="Filter by job type"),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of jobs to return",
    ),
) -> list[Job]:
    """Get a list of jobs."""
    try:
        # Get job repository (will initialize database if needed)
        job_repo = db_manager.job_repo
        
        if status:
            try:
                status_enum = JobStatus(status.upper())
                jobs = job_repo.get_jobs_by_status(status_enum, limit=limit)
            except ValueError:
                valid_statuses = ", ".join([s.value for s in JobStatus])
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}. Valid: {valid_statuses}",
                ) from None
        elif job_type:
            try:
                job_type_enum = JobType(job_type.upper())
                jobs = job_repo.get_jobs_by_type(job_type_enum, limit=limit)
            except ValueError:
                valid_types = ", ".join([t.value for t in JobType])
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid job type: {job_type}. Valid: {valid_types}",
                ) from None
        else:
            jobs = job_repo.get_recent_jobs(limit=limit)

        return [Job.from_db_job(job) for job in jobs]

    except Exception as e:
        logger.exception(f"Error retrieving jobs: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving jobs: {e!s}",
        ) from e


@app.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: int) -> Job:
    """Get a specific job by ID."""
    job_repo = db_manager.job_repo
    job = job_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    return Job.from_db_job(job)


@app.get("/jobs/{job_id}/logs", response_model=list[JobLogEntry])
async def get_job_logs(job_id: int) -> list[JobLogEntry]:
    """Get logs for a specific job."""
    job_repo = db_manager.job_repo
    job = job_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    logs = job_repo.get_job_logs(job_id)
    return [
        JobLogEntry(
            id=log.id,
            job_id=log.job_id,
            timestamp=log.timestamp,
            level=log.level,
            message=log.message,
            details=log.details,
        )
        for log in logs
    ]


# Update job endpoints
def run_update_job_background(
    job_type: str,
    from_date: str | None = None,
    max_records: int | None = None,
    use_postgres: bool | None = None,
) -> None:
    """Run an update job in the background."""
    try:
        if job_type.upper() == JobType.WORKS_UPDATE.value:
            run_works_update(
                from_date=from_date,
                max_records=max_records,
                use_postgres=use_postgres,
            )
        else:
            logger.error(f"Unsupported job type: {job_type}")
    except Exception as e:
        logger.exception(f"Error running update job: {e!s}")


@app.post("/update", response_model=Job)
async def start_update_job(
    update_request: UpdateRequest,
    background_tasks: BackgroundTasks,
) -> Job:
    """Start a data update job."""
    try:
        # Validate job type
        try:
            job_type_enum = JobType(update_request.job_type.upper())
        except ValueError:
            valid_types = ", ".join([t.value for t in JobType])
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid job type: {update_request.job_type}. "
                    f"Valid: {valid_types}"
                ),
            ) from None

        # Currently only supporting WORKS_UPDATE
        if job_type_enum != JobType.WORKS_UPDATE:
            raise HTTPException(
                status_code=400,
                detail=f"Currently only {JobType.WORKS_UPDATE.value} is supported",
            )

        # Use explicit setting if provided, otherwise use the config default
        use_postgres = (
            update_request.use_postgres
            if update_request.use_postgres is not None
            else USE_POSTGRES
        )

        # Create job (will initialize database if needed)
        job_repo = db_manager.job_repo
        job = job_repo.create_job(
            job_type=job_type_enum,
            parameters={
                "from_date": update_request.from_date,
                "max_records": update_request.max_records,
                "use_postgres": use_postgres,
            },
        )

        # Start job in background
        background_tasks.add_task(
            run_update_job_background,
            job_type=job_type_enum.value,
            from_date=update_request.from_date,
            max_records=update_request.max_records,
            use_postgres=use_postgres,
        )

        return Job.from_db_job(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error starting update job: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting update job: {e!s}",
        ) from e

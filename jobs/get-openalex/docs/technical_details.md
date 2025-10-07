# 🔧 Technical Details

This document provides technical details about the OpenAlex API system, focusing on the database models, logging system, and implementation details.

## 📋 Table of Contents
- [Database Structure](#database-structure)
  - [Job Metadata Database](#job-metadata-database)
  - [Optional OpenAlex Data Database](#optional-openalex-data-database)
- [Structured Logging System](#structured-logging-system)
  - [JSON-Formatted Logs](#json-formatted-logs)
  - [JobLogger](#joblogger)
- [Implementation Details](#implementation-details)
  - [API Implementation](#api-implementation)
  - [Incremental Update Logic](#incremental-update-logic)
  - [Error Handling](#error-handling)
  - [Background Processing](#background-processing)

## 💾 Database Structure

The system uses one required database and one optional database:

### Job Metadata Database

This SQLite database (configurable to other backends) tracks job execution history and metadata. It is always required for storing API metadata and job tracking information.

#### Job Table

```python
class Job(SQLModel, table=True):
    """Job execution metadata for tracking updates."""

    id: Optional[int] = Field(default=None, primary_key=True)
    job_type: JobType = Field(index=True)
    status: JobStatus = Field(default=JobStatus.PENDING, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    # Update statistics
    records_processed: int = Field(default=0)
    records_created: int = Field(default=0)
    records_updated: int = Field(default=0)
    records_failed: int = Field(default=0)

    # Additional metadata
    parameters: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = Field(default=None)

    # Relationships
    job_logs: List["JobLog"] = Relationship(back_populates="job")
```

#### JobLog Table

```python
class JobLog(SQLModel, table=True):
    """Detailed log entry for job execution."""

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(default="INFO")
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

    # Relationship
    job: Job = Relationship(back_populates="job_logs")
```

#### Enums

```python
class JobStatus(str, Enum):
    """Status values for job execution."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

class JobType(str, Enum):
    """Types of update jobs."""
    WORKS_UPDATE = "WORKS_UPDATE"
    AUTHORS_UPDATE = "AUTHORS_UPDATE"
    VENUES_UPDATE = "VENUES_UPDATE"
    CONCEPTS_UPDATE = "CONCEPTS_UPDATE"
    INSTITUTIONS_UPDATE = "INSTITUTIONS_UPDATE"
    FULL_UPDATE = "FULL_UPDATE"
```

### Optional OpenAlex Data Database (PostgreSQL)

> **Note**: This database is optional. The API can fetch and process data from OpenAlex without storing it.

When configured, the system can store OpenAlex data in a PostgreSQL database to provide faster access and offline capabilities.

#### Works Table

```python
class Work(SQLModel, table=True):
    __tablename__ = "openalex_works"

    id: str = Field(primary_key=True)
    title: str
    publication_date: Optional[str] = Field(default=None, index=True)
    doi: Optional[str] = Field(default=None, index=True)
    updated_date: Optional[str] = Field(default=None, index=True)
    data: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

## Structured Logging System

The system uses a sophisticated structured logging approach designed for containerized environments like Kubernetes.

### JSON-Formatted Logs

All logs are formatted as JSON objects with consistent fields:

```json
{
  "timestamp": "2023-06-15T10:30:05Z",
  "service": "openalex-api",
  "level": "INFO",
  "message": "Starting job: works_update",
  "logger": "job.works_update",
  "job_id": 123,
  "job_name": "works_update",
  "event": "job_start",
  "from_date": "2023-06-01"
}
```

This format makes it easy to filter, search, and analyze logs using tools like ELK Stack, Loki, or CloudWatch.

### JobLogger

The `JobLogger` class provides specialized logging for job execution with standardized event types:

```python
class JobLogger:
    """Enhanced logger for tracking jobs with timing and structured output."""

    def __init__(
        self,
        job_name: str,
        job_id: Optional[str] = None,
        service_name: str = "openalex-update",
    ):
        self.logger = get_logger(f"job.{job_name}", service_name)
        self.job_name = job_name
        self.job_id = job_id or int(time.time())
        self.start_time = None
        self.end_time = None

    def start_job(self, **kwargs):
        """Log job start with custom attributes."""
        self.start_time = time.time()
        self.logger.info(
            f"Starting job: {self.job_name}",
            extra={
                "job_id": self.job_id,
                "job_name": self.job_name,
                "event": "job_start",
                **kwargs,
            },
        )

    def end_job(self, status: str = "success", **kwargs):
        """Log job completion with timing information."""
        self.end_time = time.time()
        duration = (
            round(self.end_time - self.start_time, 2) if self.start_time else None
        )

        self.logger.info(
            f"Job completed: {self.job_name}",
            extra={
                "job_id": self.job_id,
                "job_name": self.job_name,
                "event": "job_end",
                "status": status,
                "duration_seconds": duration,
                **kwargs,
            },
        )

    def progress(self, current: int, total: Optional[int] = None, **kwargs):
        """Log job progress."""
        progress_pct = round((current / total) * 100, 1) if total else None

        self.logger.info(
            f"Job progress: {current}"
            + (f"/{total} ({progress_pct}%)" if total else ""),
            extra={
                "job_id": self.job_id,
                "job_name": self.job_name,
                "event": "job_progress",
                "progress_current": current,
                "progress_total": total,
                "progress_percent": progress_pct,
                **kwargs,
            },
        )
```

## Implementation Details

### API Implementation

The API implementation is designed to be modular and extensible, allowing for easy addition of new features and data sources.

### Incremental Update Logic

The update process uses the following approach to efficiently update the database:

1. Determine the starting date for the update:
   - Use the provided `from_date` if specified
   - Otherwise, find the date of the last successful update
   - Fall back to 7 days ago if no previous update exists

2. Query the OpenAlex API for works updated since the starting date:
   ```python
   filters = {
       "from_updated_date": from_date,
   }
   # Use cursor-based pagination for efficiency
   for work in iter_filtered_works_cursor(filters=filters):
       # Process work
   ```

3. For each work, check if it already exists in the database:
   - If it exists, update the existing record
   - If it doesn't exist, insert a new record

4. Track statistics and update job metadata

### Error Handling

The system implements comprehensive error handling:

1. **Global exception handling** in API routes to return appropriate HTTP status codes
2. **Per-record error handling** during updates to prevent one failed record from stopping the entire job
3. **Job status tracking** to clearly indicate success or failure
4. **Detailed error logs** with context for debugging

### Background Processing

Update jobs are executed as background tasks to allow the API to remain responsive:

```python
@app.post("/update", response_model=Job)
async def start_update_job(
    update_request: UpdateRequest, background_tasks: BackgroundTasks
):
    # Create job
    job = job_repo.create_job(
        job_type=job_type_enum,
        parameters={
            "from_date": update_request.from_date,
            "max_records": update_request.max_records,
        },
    )

    # Start job in background
    background_tasks.add_task(
        run_update_job_background,
        job_type=job_type_enum.value,
        from_date=update_request.from_date,
        max_records=update_request.max_records,
    )

    return Job.from_db_job(job)
```

This approach allows long-running updates to proceed without blocking the web server. 
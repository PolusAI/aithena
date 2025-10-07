"""Logging configuration for OpenAlex API and update jobs.

This module provides structured logging formatted as JSON for better integration
with Kubernetes and container orchestration platforms.
"""

import json
import logging
import sys
import time
from datetime import datetime
from logging import INFO

# Standard log levels
TRACE = 5


class StructuredLogFormatter(logging.Formatter):
    """Format logs as JSON for better processing in container environments."""

    def __init__(self, service_name: str = "openalex-api") -> None:
        """Initialize the JSON formatter."""
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        timestamp = datetime.fromtimestamp(record.created).isoformat()

        # Basic log data
        log_data = {
            "timestamp": timestamp,
            "service": self.service_name,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any custom fields from the record
        for key, value in record.__dict__.items():
            # Skip standard attributes and private attributes
            if key not in (
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            ) and not key.startswith("_"):
                log_data[key] = value

        return json.dumps(log_data)


def configure_logging(
    service_name: str = "openalex-api",
    level: int = INFO,
) -> logging.Logger:
    """Configure logging for containerized environments.

    Args:
        service_name: Name of the service for log identification.
        level: Logging level.
    """
    # Remove any existing handlers
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # Configure root logger
    root_logger.setLevel(level)

    # Create a handler that writes to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredLogFormatter(service_name))
    root_logger.addHandler(handler)

    # Suppress logs from other libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return root_logger


def get_logger(
    name: str,
    service_name: str = "openalex-api",
    level: int = INFO,
) -> logging.Logger:
    """Get a configured logger with the given name.

    Args:
        name: Logger name, typically __name__.
        service_name: Name of the service for log identification.
        level: Logging level.
    """
    logger = logging.getLogger(name)
    # Only configure if it hasn't been configured yet
    if not logger.handlers and not logging.getLogger().handlers:
        configure_logging(service_name, level)
    return logger


class JobLogger:
    """Enhanced logger for tracking jobs with timing and structured output."""

    def __init__(
        self,
        job_name: str,
        job_id: str | None = None,
        service_name: str = "openalex-update",
    ) -> None:
        """Initialize the job logger."""
        self.logger = get_logger(f"job.{job_name}", service_name)
        self.job_name = job_name
        self.job_id = job_id or int(time.time())
        self.start_time = None
        self.end_time = None

    def start_job(self, **kwargs: object) -> None:
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

    def end_job(self, status: str = "success", **kwargs: object) -> None:
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

    def progress(
        self,
        current: int,
        total: int | None = None,
        **kwargs: object,
    ) -> None:
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

    def info(self, message: str, **kwargs: object) -> None:
        """Log an info message with job context."""
        self.logger.info(
            message,
            extra={"job_id": self.job_id, "job_name": self.job_name, **kwargs},
        )

    def error(self, message: str, **kwargs: object) -> None:
        """Log an error message with job context."""
        self.logger.error(
            message,
            extra={"job_id": self.job_id, "job_name": self.job_name, **kwargs},
        )

    def warning(self, message: str, **kwargs: object) -> None:
        """Log a warning message with job context."""
        self.logger.warning(
            message,
            extra={"job_id": self.job_id, "job_name": self.job_name, **kwargs},
        )

    def debug(self, message: str, **kwargs: object) -> None:
        """Log a debug message with job context."""
        self.logger.debug(
            message,
            extra={"job_id": self.job_id, "job_name": self.job_name, **kwargs},
        )

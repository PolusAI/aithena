"""Command-line interface for Clinical Aithena."""

import importlib.metadata
import json
import logging
import sys
import typer

from polus.aithena.clinical_aithena.cli.commands.initdb import initdb_command
from polus.aithena.clinical_aithena.cli.commands.updatedb import updatedb_command
from polus.aithena.clinical_aithena.cli.commands.diff_study import diff_study_command
from polus.aithena.clinical_aithena.cli.commands.transform import transform_command
from polus.aithena.clinical_aithena.cli.commands.embed import embed_command


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in Kubernetes/Grafana.
    Outputs logs in JSON format for easy parsing by Loki/CloudWatch.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def configure_logging(json_logs: bool = False):
    """
    Configure logging for CLI commands.
    
    Args:
        json_logs: If True, use JSON formatting (better for K8s/Grafana).
                   If False, use human-readable format (better for local dev).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create handler that writes to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Choose formatter based on environment
    if json_logs:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Ensure logs are flushed immediately (important for K8s)
    handler.flush()


app = typer.Typer(
    name="ct-aithena",
    help="Clinical Aithena CLI - Tools for ClinicalTrials.gov data",
    no_args_is_help=True,
)


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        try:
            version = importlib.metadata.version("clinical-aithena-agent")
        except importlib.metadata.PackageNotFoundError:
            version = "dev"
        typer.echo(f"Clinical Aithena version {version}")
        raise typer.Exit()


@app.callback()
def callback(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit",
    ),
    json_logs: bool = typer.Option(
        False,
        "--json-logs",
        help="Output logs in JSON format (recommended for Kubernetes/Grafana)",
        envvar="JSON_LOGS",
    ),
):
    """
    Clinical Aithena CLI - Tools for ClinicalTrials.gov data.
    """
    # Configure logging for all commands
    configure_logging(json_logs=json_logs)


# Register commands
app.command(name="initdb")(initdb_command)
app.command(name="updatedb")(updatedb_command)
app.command(name="diff-study")(diff_study_command)
app.command(name="transform")(transform_command)
app.command(name="embed")(embed_command)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    app()

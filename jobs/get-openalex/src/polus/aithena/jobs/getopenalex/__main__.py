#!/usr/bin/env python3
"""Main entry point for get-openalex CLI.

This module provides a unified CLI interface for both S3 operations
and REST API interactions.
"""

import typer

from polus.aithena.jobs.getopenalex.logger import get_logger
from polus.aithena.jobs.getopenalex.s3.__main__ import app as s3_app

logger = get_logger(__name__)

app = typer.Typer(
    help="get-openalex - Tool for downloading OpenAlex records & using their REST API",
)

# Add the S3 commands as a sub-command
app.add_typer(s3_app, name="s3", help="Download OpenAlex snapshots from S3 Bucket")


@app.callback()
def callback() -> None:
    """Get OpenAlex records from their S3 bucket or REST API."""
    logger.info("Starting get-openalex CLI")


@app.command()
def version() -> None:
    """Show the version of get-openalex."""
    from polus.aithena.jobs.getopenalex import __version__

    typer.echo(f"get-openalex version: {__version__}")


@app.command()
def search_works(
    query: str = typer.Option(..., "--query", "-q", help="Search query for works"),
    from_date: str | None = typer.Option(
        None,
        "--from-date",
        help="Filter by publication date (YYYY-MM-DD)",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of results to return",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json, csv",
    ),
) -> None:
    """Search for works using the OpenAlex REST API."""
    from polus.aithena.jobs.getopenalex.rest.get_works import get_filtered_works_dict

    filters = {}
    if from_date:
        filters["from_publication_date"] = from_date

    logger.info(f"Searching for '{query}' with filters {filters}")
    
    # Use the correct search field for OpenAlex API
    # 'default.search' searches across multiple fields
    if query:
        filters["default.search"] = query
    
    works = get_filtered_works_dict(
        filters=filters, 
        max_results=limit,
        convert_to_model=True
    )

    if output_format == "text":
        for i, work in enumerate(works, 1):
            typer.echo(f"{i}. {work.title} ({work.publication_date})")
            typer.echo(f"   ID: {work.id}")
            typer.echo(f"   DOI: {work.doi}")
            typer.echo("")
    elif output_format == "json":
        import json

        typer.echo(json.dumps([w.model_dump() for w in works], indent=2))
    elif output_format == "csv":
        import csv
        import sys

        writer = csv.writer(sys.stdout)
        writer.writerow(["id", "title", "publication_date", "doi"])
        for work in works:
            writer.writerow([work.id, work.title, work.publication_date, work.doi])
    else:
        typer.echo(f"Unknown output format: {output_format}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind the API server to"),
    port: int = typer.Option(8000, help="Port for the API server"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
) -> None:
    """Start the OpenAlex API server."""
    from polus.aithena.jobs.getopenalex.api.run import main as start_server

    typer.echo(f"Starting API server at {host}:{port}")
    start_server(host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()

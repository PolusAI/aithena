"""Command-line interface for the get-openalex tool."""

from datetime import datetime, timedelta
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Add this import for the API server
from .api.run import start_server
from .api.database import Database, JobRepository, JobStatus
from .api.update import run_works_update
from .logger import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer()
s3_app = typer.Typer()
app.add_typer(s3_app, name="s3", help="S3 bucket operations")


@app.command("version")
def version() -> None:
    """Display the current version of get-openalex."""
    from . import __version__

    typer.echo(f"get-openalex version: {__version__}")


# Add the serve command to launch the API server
@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind the API server to"),
    port: int = typer.Option(8000, help="Port for the API server"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
) -> None:
    """Start the OpenAlex API server."""
    typer.echo(f"Starting API server at {host}:{port}")
    start_server(host=host, port=port, reload=reload)


@app.command("update")
def update(
    from_date: Optional[str] = typer.Option(
        None,
        "--from-date",
        "-f",
        help="Start date for updates (YYYY-MM-DD). If not provided, uses last successful update or 7 days ago.",
    ),
    max_records: Optional[int] = typer.Option(
        None,
        "--max-records",
        "-m",
        help="Maximum number of records to process. Default from config or 10000.",
    ),
    use_postgres: Optional[bool] = typer.Option(
        None,
        "--use-postgres/--no-postgres",
        help="Whether to store data in PostgreSQL. Default from config.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Run without actually storing data, just count records.",
    ),
) -> None:
    """Run an OpenAlex data update job.
    
    This command fetches updated works from the OpenAlex API and optionally
    stores them in a PostgreSQL database. Progress is tracked in the job database.
    
    Examples:
        # Update from last successful run
        get-openalex update
        
        # Update from specific date
        get-openalex update --from-date 2025-01-01
        
        # Update with limited records (useful for testing)
        get-openalex update --max-records 100
        
        # Count records without storing (dry run)
        get-openalex update --dry-run
    """
    try:
        # Validate date format if provided
        if from_date:
            try:
                datetime.strptime(from_date, "%Y-%m-%d")
            except ValueError:
                console.print(
                    f"[red]Error: Invalid date format '{from_date}'. Use YYYY-MM-DD[/red]"
                )
                raise typer.Exit(1)
        
        # If dry run, force no postgres
        if dry_run:
            use_postgres = False
            console.print("[yellow]Running in dry-run mode (no data will be stored)[/yellow]")
        
        # Start the update
        console.print(f"[green]Starting OpenAlex update job...[/green]")
        if from_date:
            console.print(f"  From date: {from_date}")
        else:
            console.print("  From date: [italic]auto-detect from last successful run[/italic]")
        
        if max_records:
            console.print(f"  Max records: {max_records}")
        
        if use_postgres is not None:
            console.print(f"  PostgreSQL storage: {'enabled' if use_postgres else 'disabled'}")
        
        # Run the update
        job = run_works_update(
            from_date=from_date,
            max_records=max_records,
            use_postgres=use_postgres,
        )
        
        # Display results
        console.print(f"\n[green]Update job completed![/green]")
        console.print(f"  Job ID: {job.id}")
        console.print(f"  Status: {job.status.value}")
        console.print(f"  Records processed: {job.records_processed}")
        console.print(f"  Records created: {job.records_created}")
        console.print(f"  Records updated: {job.records_updated}")
        console.print(f"  Records failed: {job.records_failed}")
        
        if job.duration_seconds:
            console.print(f"  Duration: {job.duration_seconds:.2f} seconds")
        
        if job.error_message:
            console.print(f"  [red]Error: {job.error_message}[/red]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Update cancelled by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error running update: {e}[/red]")
        logger.exception("Update command failed")
        raise typer.Exit(1)


@app.command("jobs")
def jobs(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of jobs to display"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by job status"),
    job_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by job type"),
) -> None:
    """List recent update jobs.
    
    Examples:
        # Show last 10 jobs
        get-openalex jobs
        
        # Show last 20 jobs
        get-openalex jobs --limit 20
        
        # Show only failed jobs
        get-openalex jobs --status FAILED
        
        # Show only works update jobs
        get-openalex jobs --type WORKS_UPDATE
    """
    try:
        # Initialize database
        db = Database()
        job_repo = JobRepository(db)
        
        # Get jobs based on filters
        if status:
            try:
                status_enum = JobStatus(status.upper())
                jobs_list = job_repo.get_jobs_by_status(status_enum, limit=limit)
            except ValueError:
                valid_statuses = ", ".join([s.value for s in JobStatus])
                console.print(f"[red]Invalid status: {status}. Valid options: {valid_statuses}[/red]")
                raise typer.Exit(1)
        elif job_type:
            from .api.database import JobType
            try:
                job_type_enum = JobType(job_type.upper())
                jobs_list = job_repo.get_jobs_by_type(job_type_enum, limit=limit)
            except ValueError:
                valid_types = ", ".join([t.value for t in JobType])
                console.print(f"[red]Invalid job type: {job_type}. Valid options: {valid_types}[/red]")
                raise typer.Exit(1)
        else:
            jobs_list = job_repo.get_recent_jobs(limit=limit)
        
        if not jobs_list:
            console.print("[yellow]No jobs found[/yellow]")
            return
        
        # Create table
        table = Table(title="OpenAlex Update Jobs")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="bold")
        table.add_column("Started", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Processed", style="blue", justify="right")
        table.add_column("Success Rate", style="cyan", justify="right")
        
        for job in jobs_list:
            # Format status with color
            status_color = {
                "PENDING": "yellow",
                "RUNNING": "cyan",
                "COMPLETED": "green",
                "FAILED": "red",
                "ABORTED": "magenta",
            }.get(job.status.value, "white")
            status_text = f"[{status_color}]{job.status.value}[/{status_color}]"
            
            # Format start time
            start_time = job.started_at.strftime("%Y-%m-%d %H:%M") if job.started_at else "-"
            
            # Format duration
            duration = f"{job.duration_seconds:.1f}s" if job.duration_seconds else "-"
            
            # Calculate success rate
            if job.records_processed > 0:
                success_rate = ((job.records_processed - job.records_failed) / job.records_processed) * 100
                success_rate_text = f"{success_rate:.1f}%"
            else:
                success_rate_text = "-"
            
            table.add_row(
                str(job.id),
                job.job_type.value,
                status_text,
                start_time,
                duration,
                str(job.records_processed),
                success_rate_text,
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing jobs: {e}[/red]")
        logger.exception("Jobs command failed")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

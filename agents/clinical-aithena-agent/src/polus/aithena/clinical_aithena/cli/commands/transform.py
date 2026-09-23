import logging
import sys
from typing import List, Optional

import typer
from sqlalchemy import func, exists
from sqlmodel import Session, create_engine, select

from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy
from polus.aithena.clinical_aithena.models import TrialGPTStudy
from polus.aithena.clinical_aithena.services.transform import transform_study

logger = logging.getLogger(__name__)


def transform_command(
    url: str = typer.Option(
        None,
        "--url",
        help="Database connection URL (defaults to DATABASE_URL env var)",
        envvar="DATABASE_URL",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Full refresh: Reprocess all latest studies (slow)",
    ),
    incremental: bool = typer.Option(
        True,
        "--incremental/--no-incremental",
        help="Only process new/updated studies (default)",
    ),
    nct_ids: Optional[List[str]] = typer.Option(
        None,
        "--id",
        help="Process specific NCT IDs",
    ),
    batch_size: int = typer.Option(
        100,
        "--batch-size",
        help="Number of records to commit at once",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Process but do not save to database",
    ),
):
    """
    Transform raw ClinicalTrials.gov data into TrialGPT format.
    """
    if not url:
        url = "postgresql+psycopg://postgres:CHANGE_ME_POSTGRES_PASSWORD@localhost:5432/clinical_aithena"
        typer.echo("No DATABASE_URL found, using default localhost connection")

    engine = create_engine(url, echo=False)

    # Strategy selection
    if nct_ids:
        typer.echo(f"Processing {len(nct_ids)} specific studies...")
        process_mode = "ids"
    elif full:
        typer.echo("Full refresh mode selected. Processing ALL latest studies...")
        process_mode = "full"
    else:
        typer.echo("Incremental mode selected. Processing new/updated studies...")
        process_mode = "incremental"

    with Session(engine) as session:
        # Check if trialgpt_study table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        trialgpt_exists = 'trialgpt_study' in inspector.get_table_names()
        
        if not trialgpt_exists:
            typer.echo("Note: trialgpt_study table does not exist. Creating it...")
            from sqlmodel import SQLModel
            SQLModel.metadata.create_all(engine, tables=[TrialGPTStudy.__table__])
            typer.echo("Table created successfully.")
        
        # Build query for source studies
        query = select(CTGovStudy).where(CTGovStudy.is_latest == True)

        if process_mode == "ids":
            query = query.where(CTGovStudy.nct_id.in_(nct_ids))
        elif process_mode == "incremental":
            if trialgpt_exists:
                typer.echo("Checking for new/updated studies...")
                sys.stdout.flush()
                
                # Incremental logic using NOT EXISTS (much faster than NOT IN for large datasets):
                # Find CTGovStudies where no corresponding TrialGPTStudy exists
                # This handles "new versions" because a new version creates a new CTGovStudy row with a new ID
                # So if we just check for IDs not present in the destination table, we catch all updates.
                not_exists_clause = ~exists().where(
                    TrialGPTStudy.ctgov_study_id == CTGovStudy.id
                )
                query = query.where(not_exists_clause)
            else:
                # Table was just created, process all studies
                typer.echo("Processing all studies (table is new)...")
                sys.stdout.flush()

        # Count total using optimized query
        typer.echo("Counting studies to process...")
        sys.stdout.flush()
        
        # Use the same WHERE clauses for counting (more efficient than subquery)
        count_query = select(func.count(CTGovStudy.id)).where(CTGovStudy.is_latest == True)
        
        if process_mode == "ids":
            count_query = count_query.where(CTGovStudy.nct_id.in_(nct_ids))
        elif process_mode == "incremental" and trialgpt_exists:
            not_exists_clause = ~exists().where(
                TrialGPTStudy.ctgov_study_id == CTGovStudy.id
            )
            count_query = count_query.where(not_exists_clause)
        
        total = session.exec(count_query).one()
        
        if total == 0:
            typer.echo("No studies found to process.")
            return

        typer.echo(f"Found {total:,} studies to transform.")

        # Process in batches
        processed = 0
        success = 0
        failed = 0
        skipped = 0
        last_log = 0
        
        # Adaptive log interval based on total count
        # For small incremental updates, log more frequently
        if total < 1000:
            LOG_INTERVAL = max(10, total // 10)  # Log at least every 10, or 10% of total
        else:
            LOG_INTERVAL = 1000  # Log every 1,000 studies for large batches
        
        # Use yield_per for memory efficiency with large result sets
        studies_iter = session.exec(query).yield_per(batch_size)
        
        # Batch buffer
        batch: List[TrialGPTStudy] = []

        typer.echo(f"Starting transformation (updates every {LOG_INTERVAL:,} studies)...")
        sys.stdout.flush()
        
        for study in studies_iter:
            try:
                transformed = transform_study(study)
                
                if transformed:
                    batch.append(transformed)
                    success += 1
                else:
                    skipped += 1
                    # Log failure for critical missing data?
                    # transform_study logs warnings already
            except Exception as e:
                failed += 1
                logger.error(f"Failed to transform {study.nct_id}: {e}")

            processed += 1
            
            # Periodic progress logging (works in Kubernetes, unlike tqdm)
            if processed - last_log >= LOG_INTERVAL:
                pct = (processed / total * 100) if total > 0 else 0
                typer.echo(
                    f"Progress: {processed:,}/{total:,} ({pct:.1f}%) | "
                    f"Success: {success:,} | Failed: {failed:,} | Skipped: {skipped:,}"
                )
                sys.stdout.flush()
                last_log = processed

            if len(batch) >= batch_size:
                if not dry_run:
                    _save_batch(session, batch)
                batch = []

        # Save remaining
        if batch and not dry_run:
            _save_batch(session, batch)
        
        # Final progress update if we haven't logged recently
        if processed > last_log:
            pct = (processed / total * 100) if total > 0 else 0
            typer.echo(
                f"Progress: {processed:,}/{total:,} ({pct:.1f}%) | "
                f"Success: {success:,} | Failed: {failed:,} | Skipped: {skipped:,}"
            )

    # Summary
    typer.echo("\n--- Transformation Summary ---")
    typer.echo(f"Total processed: {processed}")
    typer.echo(f"Successful:      {success}")
    typer.echo(f"Skipped (empty): {skipped}")
    typer.echo(f"Failed:          {failed}")
    
    if dry_run:
        typer.echo("\n[DRY RUN] No changes were committed to the database.")


def _save_batch(session: Session, batch: List[TrialGPTStudy]):
    """Upsert logic for TrialGPTStudy."""
    # Since we are essentially syncing from an append-only log (CTGovStudy),
    # and we keyed off the unique CTGovStudy.id (which represents a specific version),
    # we can generally just insert.
    
    # However, to be safe against re-runs or crashes, we should handle conflicts on PK (nct_id).
    # But wait, TrialGPTStudy PK is nct_id. This means it only stores the "current" state for the app.
    # It does NOT store history like CTGovStudy.
    
    # So we need to UPDATE if it exists, or INSERT if not.
    # Using session.merge() is the simplest way to handle upsert in SQLModel/SQLAlchemy ORM.
    
    for item in batch:
        session.merge(item)
    
    session.commit()
    # Note: We don't call session.expunge_all() here because the parent
    # context is still using yield_per(), which needs the session identity map.
    # The session will be closed/cleared when the parent context exits.


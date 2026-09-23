"""
Populate the database with clinical trials data.

This command fetches the latest data from ClinicalTrials.gov and updates the database.
It uses an append-only strategy:
- New versions of studies are inserted as new rows
- Existing "latest" versions are marked as not latest
- Duplicate versions (same NCT ID and update date) are skipped
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor
import hashlib
import orjson
import sys
from datetime import datetime
from typing import Dict, List

import typer
from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from polus.aithena.clinical_aithena.clients.ctgov.client import CTGovClient
from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy


async def updatedb_db(database_url: str) -> bool:
    """Update the database with the latest clinical trials.

    Strategy:
    1. Fetch all studies from ClinicalTrials.gov using sync iterator (tqdm_async blocks).
    2. For each study, check if we already have this version (based on hash).
    3. If we have it, skip.
    4. If we don't, add to batch and queue for async database writes.
    5. Separate writer task processes batches in parallel with fetching.
    """
    typer.echo(f"Connecting to database: {database_url}")

    # Create engine
    engine = create_engine(database_url, echo=False)

    # Enable pgvector extension
    typer.echo("\nEnabling pgvector extension...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()


    # Create the client
    client = CTGovClient()

    typer.echo("Getting total studies from ClinicalTrials.gov...")
    total_studies = client.stats_sync()["totalStudies"]
    typer.echo(f"Total studies: {total_studies}")

    # Pre-fetch existing latest versions to minimize DB queries
    # Map nct_id -> content_hash
    latest_versions: Dict[str, str] = {}
    typer.echo("Fetching existing study hashes...")
    try:
        with Session(engine) as session:
            statement = select(CTGovStudy.nct_id, CTGovStudy.content_hash).where(
                CTGovStudy.is_latest.is_(True)
            )
            # Use yield_per for memory-efficient streaming of large result sets
            # This fetches rows in batches instead of loading everything at once
            loaded_count = 0
            for nct_id, db_hash in session.exec(statement).yield_per(10000):
                if nct_id:
                    latest_versions[nct_id] = db_hash or ""
                    loaded_count += 1
                    # Log progress every 10,000 records
                    if loaded_count % 10000 == 0:
                        typer.echo(f"Loaded {loaded_count:,} study hashes...")
                        sys.stdout.flush()
        typer.echo(f"Loaded {len(latest_versions):,} existing study hashes")
    except Exception as e:
        typer.echo(
            f"Warning: Could not fetch existing versions (tables might not exist): {e}"
        )

    # Iterate over all studies
    # Process in batches to manage memory and transactions
    batch_size = 1000
    studies_batch: List[CTGovStudy] = []

    count_skipped = 0
    
    # Track inserts via shared dict (mutable, so the writer can update it)
    count_tracker = {"inserted": 0}

    # Create queue for asynchronous database writes
    # maxsize=2 means we can have one batch being written and one waiting
    # This provides backpressure if DB writes are slower than fetching
    # With async iterator, the event loop can properly schedule both tasks
    import asyncio
    typer.echo("Creating queue for asynchronous database writes...")
    db_queue: asyncio.Queue = asyncio.Queue(maxsize=2)

    # Start the database writer task (consumer)
    typer.echo("Starting database writer task...")
    writer_task = asyncio.create_task(
        db_writer_task(db_queue, database_url, count_tracker)
    )
    
    typer.echo("Starting study fetching...")
    
    # Helper to process studies in a non-blocking way
    async def process_studies():
        nonlocal count_skipped, studies_batch
        
        # Helper to dump model or dict
        def dump_section(section):
            if hasattr(section, "model_dump"):
                return section.model_dump(mode="json")
            return section

        # Helper to recursively sort lists for deterministic hashing
        def recursive_sort(obj):
            if isinstance(obj, dict):
                return {k: recursive_sort(v) for k, v in obj.items()}
            if isinstance(obj, list):
                # Recursively process items first
                sorted_items = [recursive_sort(x) for x in obj]
                # Sort the list using JSON string representation as key for stability
                return sorted(
                    sorted_items,
                    key=lambda x: orjson.dumps(x, option=orjson.OPT_SORT_KEYS).decode("utf-8"),
                )
            return obj
        
        # Helper to exclude version metadata fields that don't represent content changes
        def exclude_version_fields(data: dict) -> dict:
            """
            Remove fields that represent version metadata rather than content changes.
            
            Specifically excludes:
            - derivedSection.miscInfoModule.versionHolder: API's internal version timestamp
            """
            import copy
            cleaned = copy.deepcopy(data)
            
            # Remove miscInfoModule.versionHolder if it exists in derivedSection
            if "derivedSection" in cleaned and isinstance(cleaned["derivedSection"], dict):
                if "miscInfoModule" in cleaned["derivedSection"] and isinstance(cleaned["derivedSection"]["miscInfoModule"], dict):
                    if "versionHolder" in cleaned["derivedSection"]["miscInfoModule"]:
                        del cleaned["derivedSection"]["miscInfoModule"]["versionHolder"]
            
            return cleaned
        
        # Use ASYNC iterator to avoid blocking the event loop
        study_iterator = client.fetch_all_studies(
            format="json", markup_format="markdown", page_size=1000
        )
        
        # Manual progress tracking since tqdm doesn't work well with async iterators
        processed = 0
        last_log = 0
        
        async for study in study_iterator:
            processed += 1
            
            # Log progress every 1,000 studies
            if processed - last_log >= 1000:
                typer.echo(f"Processed {processed:,} studies, skipped {count_skipped:,}, queued {len(studies_batch)} in current batch")
                sys.stdout.flush()
                last_log = processed
            
            # Determine version date from the study data
            # Try lastUpdatePostDate first, then lastUpdateSubmitDate, then today
            ver_date = None

            try:
                if study.protocolSection and study.protocolSection.statusModule:
                    status = study.protocolSection.statusModule
                    if (
                        status.lastUpdatePostDateStruct
                        and status.lastUpdatePostDateStruct.date
                    ):
                        ver_date = datetime.strptime(
                            status.lastUpdatePostDateStruct.date, "%Y-%m-%d"
                        )
                    elif status.lastUpdateSubmitDate:
                        ver_date = datetime.strptime(
                            status.lastUpdateSubmitDate, "%Y-%m-%d"
                        )
            except (ValueError, TypeError):
                pass

            if not ver_date:
                # Fallback to now if we can't find a date in the record
                ver_date = datetime.now()

            # Prepare data for hashing (convert to dicts)
            # We need to serialize sections to JSON to create a stable hash
            study_data = {}

            # Gather all sections that constitute the "content"
            # We exclude metadata fields like id, version_date, is_latest, etc.
            if study.protocolSection:
                study_data["protocolSection"] = dump_section(study.protocolSection)
            if study.resultsSection:
                study_data["resultsSection"] = dump_section(study.resultsSection)
            if study.derivedSection:
                study_data["derivedSection"] = dump_section(study.derivedSection)
            if study.documentSection:
                study_data["documentSection"] = dump_section(study.documentSection)
            if study.annotationSection:
                study_data["annotationSection"] = dump_section(study.annotationSection)

            # Exclude version metadata fields before hashing
            study_data = exclude_version_fields(study_data)

            # Create deterministic hash
            # sort_keys=True ensures consistent ordering of keys
            # recursive_sort ensures consistent ordering of lists
            canonical_data = recursive_sort(study_data)
            content_json = orjson.dumps(canonical_data, option=orjson.OPT_SORT_KEYS).decode("utf-8")
            new_hash = hashlib.sha256(content_json.encode("utf-8")).hexdigest()

            # Check if we already have this version by hash
            if study.nct_id in latest_versions:
                existing_hash = latest_versions[study.nct_id]
                if existing_hash == new_hash:
                    count_skipped += 1
                    continue

            # Prepare new study record
            study.version_date = ver_date
            study.content_hash = new_hash
            study.is_latest = True

            studies_batch.append(study)

            if len(studies_batch) >= batch_size:
                # Put batch on queue for async processing
                # This will block if queue is full (providing backpressure)
                await db_queue.put(studies_batch)
                studies_batch = []

        # Send remaining batch if any
        if studies_batch:
            await db_queue.put(studies_batch)
    
    # Run the processing function
    try:
        await process_studies()
    except Exception as e:
        typer.echo(f"\nError: Error during study fetching: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise
    finally:
        typer.echo("Finalizing...")
        # Signal the writer task to stop by sending None
        await db_queue.put(None)
        
        # Wait for all queued batches to be processed
        await db_queue.join()
        
        # Wait for the writer task to complete
        await writer_task

    typer.echo(f"\nUpdate complete.")
    typer.echo(f"  New versions inserted: {count_tracker['inserted']}")
    typer.echo(f"  Existing studies skipped: {count_skipped}")

    return True


def _process_study_batch_sync(engine, studies: List[CTGovStudy]) -> int:
    """
    Process a batch of studies synchronously.
    
    Args:
        engine: SQLAlchemy engine
        studies: List of CTGovStudy objects to process
        
    Returns:
        Number of studies successfully inserted
    """
    inserted_count = 0
    
    with Session(engine) as session:
        for study in studies:
            # 1. Find existing latest version for this NCT ID and mark as not latest
            if study.nct_id:
                statement = select(CTGovStudy).where(
                    CTGovStudy.nct_id == study.nct_id, CTGovStudy.is_latest == True
                )
                existing_studies = session.exec(statement).all()
                for existing in existing_studies:
                    existing.is_latest = False
                    session.add(existing)

            # 2. Convert nested Pydantic models to dicts for JSONB columns
            # This must happen before inserting into PostgreSQL
            if study.protocolSection and not isinstance(study.protocolSection, dict):
                study.protocolSection = study.protocolSection.model_dump(mode="json")
            if study.resultsSection and not isinstance(study.resultsSection, dict):
                study.resultsSection = study.resultsSection.model_dump(mode="json")
            if study.derivedSection and not isinstance(study.derivedSection, dict):
                study.derivedSection = study.derivedSection.model_dump(mode="json")
            if study.documentSection and not isinstance(study.documentSection, dict):
                study.documentSection = study.documentSection.model_dump(mode="json")
            if study.annotationSection and not isinstance(study.annotationSection, dict):
                study.annotationSection = study.annotationSection.model_dump(mode="json")

            # 3. Add the new study
            session.add(study)
            inserted_count += 1

        # 4. Commit all changes for this batch
        session.commit()
    
    return inserted_count


def _process_study_chunk(database_url: str, studies: List[CTGovStudy]) -> int:
    """
    Process a chunk of studies in a separate process.
    
    Each process creates its own database connection and session.
    Returns the number of studies successfully inserted.
    """
    # Create a new engine for this process (engines can't be shared across processes)
    engine = create_engine(database_url, echo=False)
    
    with Session(engine) as session:
        for study in studies:
            # 1. Find existing latest version for this NCT ID and mark as not latest
            if study.nct_id:
                statement = select(CTGovStudy).where(
                    CTGovStudy.nct_id == study.nct_id, CTGovStudy.is_latest == True
                )
                existing_studies = session.exec(statement).all()
                for existing in existing_studies:
                    existing.is_latest = False
                    session.add(existing)

            # 2. Add the new study
            # Ensure ID is None to create new row (auto-increment)
            study.id = None

            # Convert nested Pydantic models to dicts for JSONB columns
            # This is CPU-intensive work that benefits from multiprocessing
            if study.protocolSection and not isinstance(study.protocolSection, dict):
                study.protocolSection = study.protocolSection.model_dump(mode="json")
            if study.resultsSection and not isinstance(study.resultsSection, dict):
                study.resultsSection = study.resultsSection.model_dump(mode="json")
            if study.derivedSection and not isinstance(study.derivedSection, dict):
                study.derivedSection = study.derivedSection.model_dump(mode="json")
            if study.documentSection and not isinstance(study.documentSection, dict):
                study.documentSection = study.documentSection.model_dump(mode="json")
            if study.annotationSection and not isinstance(
                study.annotationSection, dict
            ):
                study.annotationSection = study.annotationSection.model_dump(
                    mode="json"
                )

            session.add(study)

        session.commit()
    
    engine.dispose()
    return len(studies)


async def save_batch_async(database_url: str, batch: List[CTGovStudy]):
    """
    Save a batch of studies asynchronously using multiprocessing.
    
    Splits the batch into chunks and processes them in parallel using
    separate processes, each with its own database connection.
    """
    # Run the blocking database operations in a thread pool
    await asyncio.to_thread(_save_batch_sync, database_url, batch)


def _save_batch_sync(database_url: str, batch: List[CTGovStudy]):
    """Run the batch saving in a separate thread."""
    with ProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_process_study_chunk, database_url, batch)
        future.result()


async def db_writer_task(
    queue: asyncio.Queue, database_url: str, count_tracker: Dict[str, int]
):
    """
    Consumer task that processes batches from the queue and writes them to the database.
    
    This ensures only one database insertion happens at a time (rate limiting).
    Processes batches until it receives None as a sentinel value.
    """
    while True:
        batch = await queue.get()
        
        # None is our sentinel value to stop the consumer
        if batch is None:
            queue.task_done()
            break
        
        try:
            await save_batch_async(database_url, batch)
            count_tracker["inserted"] += len(batch)
        except Exception as e:
            typer.echo(f"\nError saving batch: {e}", err=True)
            raise e
            # Continue processing other batches even if one fails
        finally:
            queue.task_done()


def updatedb_command(
    url: str = typer.Option(
        None,
        "--url",
        help="Database connection URL (defaults to DATABASE_URL env var)",
        envvar="DATABASE_URL",
    ),
) -> None:
    """Update the database with the latest clinical trials data."""
    # Use default if no URL provided
    if not url:
        url = "postgresql+psycopg://postgres:CHANGE_ME_POSTGRES_PASSWORD@localhost:5432/clinical_aithena"
        typer.echo("No DATABASE_URL found, using default localhost connection")

    # Initialize database
    try:
        import asyncio
        success = asyncio.run(updatedb_db(url))
        if not success:
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"\nError: Error populating database: {e}", err=True)
        raise typer.Exit(code=1)

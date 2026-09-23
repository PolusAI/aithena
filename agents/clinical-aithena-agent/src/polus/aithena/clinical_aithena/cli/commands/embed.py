"""
CLI command for generating embeddings for clinical trials.

This command uses the MedCPT embedding service to generate embeddings
for trial titles and text, storing them in the database.
"""

import logging
import sys
from typing import List, Optional

import typer
from sqlmodel import Session, create_engine, select

from polus.aithena.clinical_aithena.embeddings import MedCPTService
from polus.aithena.clinical_aithena.models import TrialGPTStudy

logger = logging.getLogger(__name__)

# Suppress httpx HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)

# Log progress every N trials (for Kubernetes compatibility)
LOG_INTERVAL = 1000

def embed_command(
    database_url: str = typer.Option(
        "postgresql+psycopg://postgres:CHANGE_ME_POSTGRES_PASSWORD@localhost:5432/clinical_aithena",
        help="Database connection URL (defaults to DATABASE_URL env var)",
        envvar="DATABASE_URL",
    ),
    batch_size: int = typer.Option(
        1000,
        help="Number of trials to process in each batch",
    ),
    litellm_url: str = typer.Option(
        None,
        "--litellm-url",
        help="LiteLLM API base URL (defaults to LITELLM_API_BASE env var)",
        envvar="LITELLM_API_BASE",
    ),
    litellm_api_key: str = typer.Option(
        None,
        "--litellm-api-key",
        help="LiteLLM API key (defaults to LITELLM_API_KEY env var)",
        envvar="LITELLM_API_KEY",
    ),
    article_model: str = typer.Option(
        None,
        "--article-model",
        help="Name of the MedCPT Article Encoder model (defaults to MEDCPT_ARTICLE_MODEL env var)",
        envvar="MEDCPT_ARTICLE_MODEL",
    ),
    query_model: str = typer.Option(
        None,
        "--query-model",
        help="Name of the MedCPT Query Encoder model (defaults to MEDCPT_QUERY_MODEL env var)",
        envvar="MEDCPT_QUERY_MODEL",
    ),
    fields: str = typer.Option(
        "both",
        help="Which fields to embed: 'title', 'text', or 'both'",
    ),
    nct_ids: Optional[str] = typer.Option(
        None,
        help="Comma-separated list of NCT IDs to process (processes all if not specified)",
    ),
    resume: bool = typer.Option(
        False,
        help="Skip trials that already have embeddings",
    ),
    dry_run: bool = typer.Option(
        False,
        help="Preview changes without committing to database",
    ),
):
    """
    Generate MedCPT embeddings for clinical trials.
    
    This command generates embeddings for trial titles and/or text using the
    ncbi/MedCPT-Article-Encoder model. Embeddings are stored in the database
    for use in semantic search.
    
    Examples:
        # Generate embeddings for all trials (uses .env configuration)
        ct-aithena embed
        
        # Generate embeddings with custom LiteLLM URL
        ct-aithena embed --litellm-url http://litellm-server:4000
        
        # Generate only title embeddings
        ct-aithena embed --fields title
        
        # Generate embeddings for specific trials
        ct-aithena embed --nct-ids NCT00001372,NCT00001373
        
        # Resume interrupted embedding generation
        ct-aithena embed --resume
    """
    if dry_run:
        typer.echo("DRY RUN MODE - No changes will be committed")
        typer.echo()
    
    # Validate fields parameter
    if fields not in ["title", "text", "both"]:
        typer.echo(f"Error: Invalid --fields value: {fields}. Must be 'title', 'text', or 'both'", err=True)
        raise typer.Exit(1)
    
    embed_title = fields in ["title", "both"]
    embed_text = fields in ["text", "both"]
    
    # Initialize database connection
    typer.echo(f"Connecting to database...")
    try:
        engine = create_engine(database_url)
    except Exception as e:
        typer.echo(f"Error: Failed to connect to database: {e}", err=True)
        raise typer.Exit(1)
    
    # Initialize embedding service
    typer.echo(f"Initializing MedCPT embedding service...")
    try:
        service = MedCPTService(
            api_base=litellm_url,
            api_key=litellm_api_key,
            article_model=article_model,
            query_model=query_model,
        )
        typer.echo(f"   Article model: {service.article_model}")
        typer.echo(f"   Query model: {service.query_model}")
    except Exception as e:
        typer.echo(f"Error: Failed to initialize embedding service: {e}", err=True)
        raise typer.Exit(1)
    
    # Build query
    with Session(engine) as session:
        query = select(TrialGPTStudy)
        
        # Filter by NCT IDs if specified
        if nct_ids:
            nct_id_list = [nid.strip() for nid in nct_ids.split(",")]
            query = query.where(TrialGPTStudy.nct_id.in_(nct_id_list))
            typer.echo(f"Processing {len(nct_id_list)} specified trials")
        
        # Filter out trials that already have embeddings if resuming
        if resume:
            if embed_title and embed_text:
                query = query.where(
                    (TrialGPTStudy.title_embedding == None) | 
                    (TrialGPTStudy.text_embedding == None)
                )
            elif embed_title:
                query = query.where(TrialGPTStudy.title_embedding == None)
            elif embed_text:
                query = query.where(TrialGPTStudy.text_embedding == None)
            typer.echo("   Resume mode: Skipping trials with existing embeddings")
        
        # Count total trials
        total_trials = len(session.exec(query).all())
        
        if total_trials == 0:
            typer.echo("No trials to process")
            return
        
        typer.echo(f"Processing {total_trials} trials")
        typer.echo()
    
    # Process trials in batches
    processed = 0
    updated = 0
    failed = 0
    skipped = 0
    
    with Session(engine) as session:
        # Process in chunks for memory efficiency
        offset = 0
        
        last_log = 0

        while offset < total_trials:
            # Fetch batch
            batch_query = query.offset(offset).limit(batch_size)
            trials = session.exec(batch_query).all()
            
            if not trials:
                break
            
            # Prepare batch data
            title_batch = []
            text_batch = []
            trial_ids = []
            
            for trial in trials:
                if not trial.title or not trial.text:
                    logger.warning(f"Trial {trial.nct_id} missing title or text, skipping")
                    skipped += 1
                    continue
                
                trial_ids.append(trial.nct_id)
                
                if embed_title:
                    title_batch.append((trial.title, trial.text))  # MedCPT encodes [title, text] pairs
                
                if embed_text:
                    text_batch.append((trial.title, trial.text))
            
            if not trial_ids:
                offset += batch_size
                continue
            
            try:
                # Generate embeddings
                title_embeddings = []
                text_embeddings = []
                
                if embed_title and title_batch:
                    title_embeddings = service.encode_articles_batch(
                        title_batch, batch_size=batch_size
                    )
                
                if embed_text and text_batch:
                    text_embeddings = service.encode_articles_batch(
                        text_batch, batch_size=batch_size
                    )
                
                # Update trials in database
                for i, nct_id in enumerate(trial_ids):
                    trial = session.get(TrialGPTStudy, nct_id)
                    if trial:
                        if embed_title and i < len(title_embeddings):
                            trial.title_embedding = title_embeddings[i]
                        if embed_text and i < len(text_embeddings):
                            trial.text_embedding = text_embeddings[i]
                        updated += 1
                
                # Commit batch
                if not dry_run:
                    session.commit()
                
                processed += len(trial_ids)
                
                # Progress update
                progress_pct = (processed / total_trials) * 100
                typer.echo(
                    f"Progress: {processed:,}/{total_trials:,} ({progress_pct:.1f}%) | "
                    f"Updated: {updated:,} | Failed: {failed:,} | Skipped: {skipped:,}"
                )
                sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"Failed to process batch starting at offset {offset}: {e}")
                failed += len(trial_ids)
                session.rollback()
            
            offset += batch_size
    
    # Cleanup
    service.unload_models()
    
    # Summary
    typer.echo("\n--- Embedding Generation Summary ---")
    typer.echo(f"Total processed: {processed}")
    typer.echo(f"Updated:         {updated}")
    typer.echo(f"Failed:          {failed}")
    typer.echo(f"Skipped:         {skipped}")
    
    if dry_run:
        typer.echo()
        typer.echo("DRY RUN - No changes were committed to the database")
    
    if failed > 0:
        typer.echo()
        typer.echo(f"Warning: {failed} trials failed to process. Check logs for details.")
        raise typer.Exit(1)
    
    typer.echo()
    typer.echo("Transformation complete.")


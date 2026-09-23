"""
Initialize the database with tables and indexes for Clinical Aithena.

This command creates the ctgovstudy table with:
- Generated columns for frequently queried fields
- B-tree indexes on generated columns
- GIN indexes on JSONB columns
- Composite indexes for common query patterns
"""

import os
import typer
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine
from sqlalchemy import text

from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy  # noqa
from polus.aithena.clinical_aithena.models import TrialGPTStudy  # noqa

# Load environment variables from .env file
load_dotenv()


def init_db(database_url: str, drop_existing: bool = False) -> bool:
    """
    Initialize the database with tables and indexes.

    Args:
        database_url: PostgreSQL connection URL
        drop_existing: If True, drop existing tables before creating

    Returns:
        True if successful, False otherwise
    """
    typer.echo(f"Connecting to database: {database_url}")

    # Create engine
    engine = create_engine(database_url, echo=False)

    # Enable required extensions
    typer.echo("\nEnabling extensions...")
    pg_search_available = False
    with engine.connect() as conn:
        # Required extensions
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        typer.echo("  + vector extension enabled")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        typer.echo("  + pg_trgm extension enabled")
        
        # Optional: pg_search (ParadeDB) - only available with ParadeDB installation
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_search"))
            pg_search_available = True
            typer.echo("  + pg_search extension enabled (BM25 search via ParadeDB)")
        except Exception as e:
            typer.echo("  Warning: pg_search extension not available (requires ParadeDB)")
            typer.echo("    BM25 search will use fallback implementation")
        
        conn.commit()

    # Drop tables if requested
    if drop_existing:
        typer.echo("\nWarning: Dropping existing tables...")
        SQLModel.metadata.drop_all(engine)

    # Create all tables with indexes
    typer.echo("\nCreating tables and indexes...")
    SQLModel.metadata.create_all(engine)

    # Verify table creation
    typer.echo("\nVerifying table creation...")
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
            FROM pg_tables
            WHERE tablename = 'ctgovstudy'
        """
            )
        )
        row = result.fetchone()
        if row:
            typer.echo(f"Table 'ctgovstudy' created successfully")
            typer.echo(f"  Schema: {row[0]}, Size: {row[2]}")
        else:
            typer.echo("Error: Table 'ctgovstudy' not found!")
            return False

    # Verify indexes
    typer.echo("\nVerifying indexes...")
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'ctgovstudy'
            ORDER BY indexname
        """
            )
        )
        indexes = result.fetchall()

        if indexes:
            typer.echo(f"Found {len(indexes)} indexes:")
            for idx in indexes:
                typer.echo(f"  - {idx[0]}")
                if "gin" in idx[1].lower():
                    typer.echo(f"    Type: GIN")
                elif "btree" in idx[1].lower() or idx[0].startswith("idx_"):
                    typer.echo(f"    Type: B-tree")
        else:
            typer.echo("Error: No indexes found")

    # Show generated columns
    typer.echo("\nVerifying generated columns...")
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT 
                column_name,
                data_type,
                is_generated,
                generation_expression
            FROM information_schema.columns
            WHERE table_name = 'ctgovstudy'
            AND is_generated = 'ALWAYS'
            ORDER BY ordinal_position
        """
            )
        )
        gen_cols = result.fetchall()

        if gen_cols:
            typer.echo(f"Found {len(gen_cols)} generated columns:")
            for col in gen_cols:
                typer.echo(f"  - {col[0]} ({col[1]})")
        else:
            typer.echo("Error: No generated columns found")

    # Verify TrialGPT table and vector indexes
    typer.echo("\nVerifying TrialGPT table...")
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT tablename
            FROM pg_tables
            WHERE tablename = 'trialgpt_study'
        """
            )
        )
        row = result.fetchone()
        if row:
            typer.echo(f"Table 'trialgpt_study' created successfully")
        else:
            typer.echo("Note: Table 'trialgpt_study' not found (optional)")

    # Verify HNSW indexes for vector search
    typer.echo("\nVerifying vector indexes...")
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'trialgpt_study'
            AND indexdef LIKE '%hnsw%'
            ORDER BY indexname
        """
            )
        )
        hnsw_indexes = result.fetchall()

        if hnsw_indexes:
            typer.echo(f"Found {len(hnsw_indexes)} HNSW indexes for vector search:")
            for idx in hnsw_indexes:
                typer.echo(f"  - {idx[0]}")
                # Extract index parameters
                if "m = 16" in idx[1]:
                    typer.echo(f"    Parameters: m=16, ef_construction=64 (balanced)")
        else:
            typer.echo("Note: No HNSW indexes found (will be created when table is populated)")

    # Create BM25 search index using pg_search (only if available)
    if pg_search_available:
        typer.echo("\nCreating BM25 search index...")
        with engine.connect() as conn:
            # Check if TrialGPTStudy table exists before creating index
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'trialgpt_study'
                )
            """
                )
            )
            table_exists = result.scalar()
            
            if table_exists:
                # Create BM25 index on title, text, and metadata fields
                try:
                    conn.execute(
                        text(
                            """
                        CREATE INDEX IF NOT EXISTS idx_trialgpt_bm25_search 
                        ON trialgpt_study 
                        USING bm25 (nct_id, title, text, metadata_json)
                        WITH (key_field='nct_id')
                    """
                        )
                    )
                    conn.commit()
                    typer.echo("  + BM25 search index created: idx_trialgpt_bm25_search")
                except Exception as e:
                    typer.echo(f"  Warning: Failed to create BM25 index: {e}")
            else:
                typer.echo("  Note: TrialGPTStudy table not found, skipping BM25 index")

    typer.echo("\nDatabase initialization complete!")
    typer.echo("\nNext steps:")
    typer.echo("  1. Run 'ct-aithena updatedb' to download trials from ClinicalTrials.gov")
    typer.echo("  2. Run 'ct-aithena transform' to transform trials to TrialGPT format")
    typer.echo("  3. Run 'ct-aithena embed' to generate embeddings for vector search")
    
    if pg_search_available:
        typer.echo("\n+ BM25 search is ready via pg_search extension (zero first-query penalty)")
    else:
        typer.echo("\nWarning: BM25 search will use in-memory fallback (first query builds index)")

    return True


def initdb_command(
    url: str = typer.Option(
        None,
        "--url",
        help="Database connection URL (defaults to DATABASE_URL env var)",
        envvar="DATABASE_URL",
    ),
    drop: bool = typer.Option(
        False,
        "--drop",
        help="Drop existing tables before creating (Warning:  DESTRUCTIVE!)",
    ),
):
    """
    Initialize the database with tables and indexes.

    Creates the ctgovstudy table with:
    - JSONB columns for document storage
    - Generated columns for frequently queried fields
    - B-tree indexes for fast exact/range queries
    - GIN indexes for flexible JSON queries
    - Composite indexes for common query patterns

    By default, reads DATABASE_URL from environment or .env file.
    For psycopg3 (recommended): postgresql+psycopg://user:pass@host:port/db
    For psycopg2 (legacy): postgresql://user:pass@host:port/db
    """
    # Use default if no URL provided
    if not url:
        url = "postgresql+psycopg://postgres:CHANGE_ME_POSTGRES_PASSWORD@localhost:5432/clinical_aithena"
        typer.echo("No DATABASE_URL found, using default localhost connection")
    # Confirm if drop is requested
    if drop:
        confirm = typer.confirm(
            "WARNING: This will DROP all existing tables! Are you sure?",
            abort=True,
        )
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit(code=1)

    # Initialize database
    try:
        success = init_db(url, drop_existing=drop)
        if not success:
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"\nError: initializing database: {e}", err=True)
        raise typer.Exit(code=1)

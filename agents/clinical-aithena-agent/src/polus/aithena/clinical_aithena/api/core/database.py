"""Database connection and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from .config import settings

# ---------------------------------------------------------------------------
# Async engine (used by search / stats / health routes)
# ---------------------------------------------------------------------------

# Convert postgresql+psycopg:// to postgresql+asyncpg:// for async support
async_database_url = settings.database_url.replace(
    "postgresql+psycopg://", "postgresql+asyncpg://"
)

engine = create_async_engine(
    async_database_url,
    echo=False,
    future=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# ---------------------------------------------------------------------------
# Sync engine (used by the GARDIAN pipeline which relies on sync SQLModel)
# ---------------------------------------------------------------------------

sync_engine = create_engine(
    settings.database_url,
    echo=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    
    Yields:
        AsyncSession: Database session for async operations.
    """
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def get_db_context():
    """
    Context manager for database sessions outside of FastAPI dependencies.
    
    Yields:
        AsyncSession: Database session for async operations.
    """
    async with async_session_maker() as session:
        yield session


@contextmanager
def get_sync_session():
    """Context manager that provides a synchronous SQLModel session.

    Used by the GARDIAN matching pipeline which requires a sync
    ``sqlmodel.Session`` for retrieval and trial lookups.
    """
    with Session(sync_engine) as session:
        yield session


async def close_db():
    """Close database connections."""
    await engine.dispose()
    sync_engine.dispose()


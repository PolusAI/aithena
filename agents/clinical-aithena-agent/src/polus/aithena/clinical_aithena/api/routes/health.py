"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """
    Health check endpoint.
    
    Verifies that the API is running and can connect to the database.
    
    Returns:
        dict: Status information including database connectivity.
    """
    try:
        # Test database connection
        result = await session.execute(text("SELECT 1"))
        result.scalar()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
    }


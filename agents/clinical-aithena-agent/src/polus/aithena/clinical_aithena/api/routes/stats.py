"""Statistics endpoint for clinical trials database."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import case, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from polus.aithena.clinical_aithena.clients.ctgov.models import (
    CTGovStudy,
    Status,
    StudyType,
)
from ..core.database import get_session

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("")
async def get_stats(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Get statistics about clinical trials in the database.

    Returns aggregated statistics from the database including:
    - Total number of studies
    - Number of recruiting studies
    - Number of interventional studies
    - Number of observational studies

    Returns:
        dict: Statistics about clinical trials including:
            - total: Total number of studies (latest versions only)
            - recruiting: Number of currently recruiting studies
            - interventional: Number of interventional studies
            - observational: Number of observational studies

    Example:
        ```bash
        curl http://localhost:8000/stats
        ```
    """
    # Single query with conditional aggregation (FILTER-style via CASE).
    # This replaces 4 separate COUNT queries with one table scan.
    query = select(
        func.count().label("total"),
        func.count(
            case(
                (col(CTGovStudy.overall_status) == Status.RECRUITING, 1),
            )
        ).label("recruiting"),
        func.count(
            case(
                (col(CTGovStudy.study_type) == StudyType.INTERVENTIONAL, 1),
            )
        ).label("interventional"),
        func.count(
            case(
                (col(CTGovStudy.study_type) == StudyType.OBSERVATIONAL, 1),
            )
        ).label("observational"),
    ).where(col(CTGovStudy.is_latest) == True)  # noqa: E712

    result = await session.execute(query)
    row = result.one()

    return {
        "total": row.total,
        "recruiting": row.recruiting,
        "interventional": row.interventional,
        "observational": row.observational,
    }


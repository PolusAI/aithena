"""Search endpoint for querying clinical trials from the database."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from polus.aithena.clinical_aithena.clients.ctgov.models import CTGovStudy
from ..core.database import get_session

router = APIRouter(prefix="/search", tags=["search"])


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    total: int
    page: int
    page_size: int
    total_pages: int
    results: list[dict]


@router.get(
    "",
    response_model=SearchResponse,
    responses={
        200: {
            "description": "Successful search with paginated results",
            "content": {
                "application/json": {
                    "examples": {
                        "all_trials": {
                            "summary": "Get all trials (default pagination)",
                            "description": "Returns first page of all trials "
                            "with default page size of 10",
                            "value": {
                                "total": 562856,
                                "page": 1,
                                "page_size": 10,
                                "total_pages": 56286,
                                "results": [
                                    {
                                        "nct_id": "NCT06900595",
                                        "brief_title": "Testing the Addition "
                                        "of an Anti-Cancer Drug...",
                                        "overall_status": "RECRUITING",
                                    }
                                ],
                            },
                        },
                        "keyword_search": {
                            "summary": "Search by keyword",
                            "description": "Search for trials containing "
                            "'cancer' in the title",
                            "value": {
                                "total": 47673,
                                "page": 1,
                                "page_size": 10,
                                "total_pages": 4768,
                                "results": [
                                    {
                                        "nct_id": "NCT06900595",
                                        "brief_title": "Testing the Addition "
                                        "of an Anti-Cancer Drug...",
                                        "overall_status": "RECRUITING",
                                    }
                                ],
                            },
                        },
                        "paginated": {
                            "summary": "Paginated results",
                            "description": "Get page 2 with custom page size",
                            "value": {
                                "total": 11101,
                                "page": 2,
                                "page_size": 20,
                                "total_pages": 556,
                                "results": [],
                            },
                        },
                    }
                }
            },
        }
    },
)
async def search_trials(
    keyword: Optional[str] = Query(
        None,
        description="Optional keyword to filter trials by title. "
        "If not provided, returns all trials.",
        openapi_examples={
            "none": {
                "summary": "No filter",
                "description": "Returns all trials",
                "value": None,
            },
            "cancer": {
                "summary": "Search cancer",
                "description": "Find trials about cancer",
                "value": "cancer",
            },
            "diabetes": {
                "summary": "Search diabetes",
                "description": "Find trials about diabetes",
                "value": "diabetes",
            },
            "heart": {
                "summary": "Search heart",
                "description": "Find trials about heart conditions",
                "value": "heart",
            },
        },
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed). Must be >= 1.",
        openapi_examples={
            "first_page": {
                "summary": "First page",
                "description": "Get the first page of results",
                "value": 1,
            },
            "second_page": {
                "summary": "Second page",
                "description": "Get the second page of results",
                "value": 2,
            },
        },
    ),
    page_size: int = Query(
        10,
        ge=1,
        le=100,
        description="Number of results per page. Min 1, max 100.",
        openapi_examples={
            "default": {
                "summary": "Default (10)",
                "description": "Default page size",
                "value": 10,
            },
            "medium": {
                "summary": "Medium (20)",
                "description": "20 results per page",
                "value": 20,
            },
            "large": {
                "summary": "Large (50)",
                "description": "50 results per page",
                "value": 50,
            },
        },
    ),
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    """
    Search clinical trials in the database.

    Returns paginated results of clinical trials, optionally filtered by
    keyword in the title. Results are ordered by most recent update
    (version_date) descending.

    Query Parameters:
        keyword: Optional keyword to filter by title (case-insensitive).
            If not provided, returns all trials.
        page: Page number (1-indexed). Default is 1.
        page_size: Number of results per page (1-100). Default is 10.

    Returns:
        SearchResponse containing:
            - total: Total number of matching trials
            - page: Current page number
            - page_size: Number of results per page
            - total_pages: Total number of pages
            - results: List of trial objects (full CTGovStudy data)

    Security:
        - Uses SQLAlchemy parameterized queries to prevent SQL injection
        - Read-only database access (when configured with read-only user)

    Example:
        ```bash
        # Get all trials (first page)
        curl http://localhost:8000/search

        # Search for "cancer" in title
        curl http://localhost:8000/search?keyword=cancer

        # Get page 2 with 20 results per page
        curl http://localhost:8000/search?page=2&page_size=20

        # Search "diabetes" on page 3
        curl http://localhost:8000/search?keyword=diabetes&page=3
        ```
    """
    # Build base filter conditions
    conditions = [col(CTGovStudy.is_latest) == True]  # noqa: E712

    # Add keyword filter if provided (case-insensitive)
    if keyword:
        # Use ilike for case-insensitive pattern matching
        # Parameterized query prevents SQL injection
        conditions.append(col(CTGovStudy.brief_title).ilike(f"%{keyword}%"))

    # Lightweight COUNT query (no ORDER BY, no subquery wrapping)
    count_query = (
        select(func.count())
        .select_from(CTGovStudy)
        .where(*conditions)
    )
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size  # Ceiling division

    # Fetch the page of results (ORDER BY only applied here)
    data_query = (
        select(CTGovStudy)
        .where(*conditions)
        .order_by(col(CTGovStudy.version_date).desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(data_query)
    trials = result.scalars().all()

    # Convert SQLModel instances to dictionaries
    results = [trial.model_dump() for trial in trials]

    return SearchResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )

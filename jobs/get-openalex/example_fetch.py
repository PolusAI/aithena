"""Example script for fetching OpenAlex works asynchronously."""

import asyncio
import logging
import traceback
from typing import Any

from polus.aithena.jobs.getopenalex.oa_rest.api_direct import PyalexWork
from polus.aithena.jobs.getopenalex.oa_rest.api_direct import Works
from polus.aithena.jobs.getopenalex.oa_rest.api_direct import _process_work
from polus.aithena.jobs.getopenalex.oa_rest.api_direct import (
    _validate_pagination_params,
)
from polus.aithena.jobs.getopenalex.oa_rest.api_direct import async_api_session

# Set up logging to see more details
logging.basicConfig(level=logging.INFO)


async def get_openalex_works_async(
    filters: dict[str, Any],
    per_page: int = 25,
    max_results: int | None = None,
    convert_to_model: bool = True,
) -> list[PyalexWork | dict]:
    """Asynchronously get works from OpenAlex API.

    This fixed implementation handles the current API response format
    which returns a list of works directly instead of a dictionary with metadata.

    Args:
        filters: Dictionary of filters to apply
        per_page: Number of results per page
        max_results: Maximum number of results to return
        convert_to_model: Whether to convert works to model objects

    Returns:
        List of works
    """
    per_page, max_results = _validate_pagination_params(per_page, max_results)
    logging.info(f"Getting works with filters: {filters}")

    query = Works().filter(**filters)

    # Directly fetch the first page to see how many items we'll get
    first_page = await asyncio.to_thread(query.get, page=1, per_page=per_page)

    # Modern API returns a list of works directly
    all_works = []
    page_num = 1

    # Process first page items with proper slicing for max_results
    if max_results is not None:
        first_page_slice = first_page[:max_results]
    else:
        first_page_slice = first_page

    first_page_items = [
        _process_work(PyalexWork(item), convert_to_model) for item in first_page_slice
    ]
    all_works.extend(first_page_items)

    # If we need more results and haven't reached max_results
    remaining = max_results - len(all_works) if max_results is not None else None
    while remaining is None or remaining > 0:
        page_num += 1
        next_page = await asyncio.to_thread(query.get, page=page_num, per_page=per_page)

        # Stop if no more results
        if not next_page:
            break

        # Process next page items with proper slicing for remaining items
        next_page_slice = next_page[:remaining] if remaining is not None else next_page

        page_items = [
            _process_work(PyalexWork(item), convert_to_model)
            for item in next_page_slice
        ]

        # If we got no items, we're done
        if not page_items:
            break

        all_works.extend(page_items)

        # Update remaining count
        if remaining is not None:
            remaining -= len(page_items)
            if remaining <= 0:
                break

        # Add a small delay to respect rate limits
        await asyncio.sleep(0.2)

    logging.info(f"Retrieved {len(all_works)} works")
    return all_works


async def main() -> None:
    """Main function to demonstrate retrieving works from OpenAlex."""
    try:
        async with async_api_session():
            logging.info("Fetching works...")

            # Using a working filter format
            works = await get_openalex_works_async(
                filters={"publication_year": 2023},
                per_page=10,
                max_results=20,
            )

            logging.info(f"\nRetrieved {len(works)} works:")
            for _, work in enumerate(works[:10]):  # Show first 10 only
                # Safely get title attribute from either dict or object
                if hasattr(work, "title"):
                    # It's a Work object
                    title = work.title
                elif isinstance(work, dict) and "title" in work:
                    # It's a dictionary
                    title = work["title"]
                else:
                    # Unknown format
                    title = str(work)

                logging.info(f"- {title}")
    except RuntimeError as e:  # Catch a more specific error if possible
        logging.error(f"Error occurred: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

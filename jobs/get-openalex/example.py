"""Example script demonstrating asynchronous fetching of OpenAlex works."""

import asyncio
import logging

from polus.aithena.jobs.getopenalex.oa_rest.api_direct import api_session
from polus.aithena.jobs.getopenalex.oa_rest.api_direct import get_filtered_works_async
from polus.aithena.jobs.getopenalex.oa_rest.metrics import metrics_collector


# Example of using the improved API with async and metrics
async def fetch_recent_works() -> None:
    """Fetches recent works from OpenAlex asynchronously."""
    # Use context manager for proper session handling
    async with api_session():
        # Get works asynchronously
        works = await get_filtered_works_async(
            filters={"from_publication_date": "2023-01-01", "is_open_access": True},
            per_page=100,
            max_results=500,
        )
        # Process works
        for work in works:
            logging.info(f"Fetched work: {work.title}")

        # Get performance metrics
        logging.info(metrics_collector.get_summary())


# Run the async function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(fetch_recent_works())

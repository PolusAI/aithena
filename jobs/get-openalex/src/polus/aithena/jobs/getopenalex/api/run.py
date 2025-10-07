#!/usr/bin/env python3
"""Run the OpenAlex API server."""
from typing import Annotated

import typer
import uvicorn

from polus.aithena.jobs.getopenalex.logger import get_logger
from polus.aithena.jobs.getopenalex.config import API_HOST
from polus.aithena.jobs.getopenalex.config import API_PORT

logger = get_logger(__name__)


def main(
    host: Annotated[
        str, typer.Option(help="Host to bind the API server to")
    ] = API_HOST,
    port: Annotated[int, typer.Option(help="Port for the API server")] = API_PORT,
    reload: Annotated[
        bool, typer.Option(help="Enable auto-reload for development")
    ] = False,
) -> None:
    """Start the OpenAlex API server."""
    logger.info(f"Starting OpenAlex API server at http://{host}:{port}")
    logger.info(f"API docs will be available at http://{host}:{port}/docs")

    uvicorn.run(
        "polus.aithena.jobs.getopenalex.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    typer.run(main)

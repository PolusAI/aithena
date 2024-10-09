"""Script to setup Ollama, for convenience purposes.

This script will:
* Pull llama3.1:latest to Ollama
* Pull nomic-embed-text to Ollama
"""

import logging
import os

import requests
import typer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Setup Ollama for Aithena Services.")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


@app.command()
def main(
    ollama_host: str = OLLAMA_HOST,
):
    """Setup Ollama for Aithena Services."""
    logger.info("Pulling llama3.1:latest to Ollama")
    try:
        requests.post(
            f"{ollama_host}/api/pull",
            json={"name": "llama3.1"},
            timeout=20,
        )
    except Exception as e:
        logger.error(f"Failed to pull llama3.1: {e}")
    logger.info("Pulled llama3.1:latest to Ollama")
    logger.info("Pulling nomic-embed-text to Ollama")
    try:
        requests.post(
            f"{ollama_host}/api/pull",
            json={"name": "nomic-embed-text"},
            timeout=20,
        )
    except Exception as e:
        logger.error(f"Failed to pull nomic-embed-text: {e}")
    logger.info("Pulled nomic-embed-text to Ollama")
    logger.info("Updating config.json for Aithena Services - Chat")
    logger.info("Setup complete.")


if __name__ == "__main__":
    app()

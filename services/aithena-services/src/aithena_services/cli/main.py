"""Command-line interface for aithena-services."""

import argparse
import importlib.metadata
import os
import sys
import logging
import uvicorn
from typing import List, Optional
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from aithena_services.config import AITHENA_LOG_LEVEL

logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)


def get_version() -> str:
    """Return the package version."""
    try:
        return importlib.metadata.version("aithena-services")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


def serve_command(args: argparse.Namespace) -> None:
    """Run the aithena-services API server."""
    # Try to load .env from current directory, or check in parent directories
    dotenv_path = find_dotenv(raise_error_if_not_found=False)
    if dotenv_path:
        logger.info(f"Loading environment variables from {dotenv_path}")
        load_dotenv(dotenv_path, override=True)
    else:
        # Also check if there's a .env in the current working directory
        cwd_env = Path(os.getcwd()) / ".env"
        if cwd_env.exists():
            logger.info(f"Loading environment variables from {cwd_env}")
            load_dotenv(cwd_env, override=True)
        else:
            logger.warning("No .env file found. Using default values.")

    logger.info(f"Starting aithena-services API server on {args.host}:{args.port}")
    uvicorn.run(
        "aithena_services.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="aithena-services CLI")
    parser.add_argument(
        "--version", action="store_true", help="Show the version and exit"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Run the API server")
    serve_parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind to"
    )
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload on code changes"
    )
    serve_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    serve_parser.add_argument(
        "--env-file",
        type=str,
        help="Path to .env file (default: auto-detect)",
    )
    serve_parser.set_defaults(func=serve_command)

    args = parser.parse_args(argv)

    if args.version:
        print(f"aithena-services version {get_version()}")
        return 0

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    # If env-file is provided, load it
    if hasattr(args, "env_file") and args.env_file:
        env_path = Path(args.env_file)
        if env_path.exists():
            logger.info(f"Loading environment variables from {env_path}")
            load_dotenv(env_path, override=True)
        else:
            logger.error(f"Specified .env file not found: {env_path}")
            return 1

    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

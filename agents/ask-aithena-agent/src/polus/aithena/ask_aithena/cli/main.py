"""Command-line interface for the Ask Aithena agent."""

import argparse
import importlib.metadata
import logging
import sys
import uvicorn
from typing import List, Optional

from polus.aithena.ask_aithena.config import AITHENA_LOG_LEVEL
logger = logging.getLogger(__name__)
logger.setLevel(AITHENA_LOG_LEVEL)


def get_version() -> str:
    """Return the package version."""
    try:
        return importlib.metadata.version("ask_aithena")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


def serve_command(args: argparse.Namespace) -> None:
    """Run the Ask Aithena API server."""

    logger.info(f"Starting Ask Aithena API server on {args.host}:{args.port}")
    uvicorn.run(
        "polus.aithena.ask_aithena.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Ask Aithena CLI")
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
    serve_parser.set_defaults(func=serve_command)

    args = parser.parse_args(argv)

    if args.version:
        print(f"Ask Aithena version {get_version()}")
        return 0

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

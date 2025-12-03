# Project Structure

This document describes the current structure of the Aithena Services codebase, focusing on the `src/aithena_services` package and its memory-focused functionality.

## Overview

Aithena Services is now focused primarily on providing vector memory functionality through PostgreSQL with the pgvector extension. The project structure reflects this specialization.

## Directory Structure

```
src/
└── aithena_services/
    ├── __init__.py        - Package initialization
    ├── cli/               - Command-line interface
    │   ├── __init__.py
    │   └── main.py        - CLI entry point
    ├── api/               - FastAPI endpoints
    │   ├── __init__.py
    │   └── app.py         - API definitions and application factory
    ├── memory/            - Vector database functionality
    │   ├── __init__.py
    │   └── pgvector.py    - PostgreSQL/pgvector implementation
    └── config.py          - Configuration settings
```

## Key Components

### CLI Module

The `cli/` directory contains the command-line interface implementation.
- `main.py`: Defines the `aithena-services` command and the `serve` subcommand to start the API server.

### API Module

The `api/` directory contains the FastAPI application and endpoint definitions. The main API endpoints are:

- `GET /health` - Health check endpoint
- `POST /memory/pgvector/search_works` - Search for works by similarity with optional filters
- `POST /memory/pgvector/get_article_by_doi` - Get an article by its DOI

These endpoints are defined in `api/app.py`.

### Memory Module

The `memory/` directory contains the implementation of the vector database functionality. The key file is `pgvector.py`, which provides:

- Database connection management (asyncpg pool)
- Vector similarity search functions
- Support for filtering by language and publication year
- Article retrieval by DOI

## Key Files

### api/app.py

This file defines the FastAPI application and endpoints for the memory functionality. It includes:

- FastAPI app initialization with lifespan manager
- Endpoint definitions for vector search and DOI lookup
- Error handling

### memory/pgvector.py

This file implements the core vector database functionality:

- PostgreSQL connection handling with `asyncpg`
- pgvector similarity search implementation
- Query construction with filters (language, year)
- DOI normalization and lookup

### cli/main.py

Entry point for the application:
- Parses command line arguments
- Loads environment variables
- Starts the uvicorn server

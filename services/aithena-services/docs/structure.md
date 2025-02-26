# Project Structure

This document describes the current structure of the Aithena Services codebase, focusing on the `src/aithena_services` package and its memory-focused functionality.

## Overview

Aithena Services is now focused primarily on providing vector memory functionality through PostgreSQL with the pgvector extension. The project structure reflects this specialization.

## Directory Structure

```
src/
└── aithena_services/
    ├── __init__.py        - Package initialization
    ├── api/               - FastAPI endpoints
    │   ├── __init__.py
    │   └── main.py        - API definitions
    ├── memory/            - Vector database functionality
    │   ├── __init__.py
    │   └── pgvector.py    - PostgreSQL/pgvector implementation
    └── common/            - Shared utilities
        ├── __init__.py
        └── azure.py       - Azure-related helpers
```

## Key Components

### API Module

The `api/` directory contains the FastAPI application and endpoint definitions. The main API endpoints are:

- `POST /memory/pgvector/search` - Search for similar vectors
- `POST /memory/pgvector/search_work_ids` - Search for work IDs
- `POST /memory/pgvector/search_works` - Search for works

These endpoints are defined in `api/main.py` and provide the interface for interacting with the vector database.

### Memory Module

The `memory/` directory contains the implementation of the vector database functionality. The key file is `pgvector.py`, which provides:

- Database connection management
- Vector similarity search functions
- Work object handling
- Vector operation utilities

### Common Module

The `common/` directory contains shared utilities and helpers used across the project, such as Azure-related helpers in `azure.py`.

## Key Files

### api/main.py

This file defines the FastAPI application and endpoints for the memory functionality. It includes:

- FastAPI app initialization
- CORS middleware configuration
- API endpoint definitions for vector search operations
- Error handling

### memory/pgvector.py

This file implements the core vector database functionality:

- PostgreSQL connection handling
- pgvector similarity search implementation
- Work object serialization/deserialization
- Vector search optimization

## Development Workflow

When working on Aithena Services, focus on:

1. Enhancing the memory and vector database functionality
2. Optimizing PostgreSQL and pgvector operations
3. Improving the API endpoints for memory operations

## Integration Points

When deployed with the complete stack:

1. LiteLLM communicates with Aithena Services through the memory API endpoints
2. Aithena Services connects to the PostgreSQL/pgvector database
3. Client applications use either LiteLLM (for model operations) or Aithena Services (for memory operations) as needed 
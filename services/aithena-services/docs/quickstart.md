# Quick Start Guide

This guide will help you get Aithena Services up and running quickly. Aithena Services now focuses on providing vector memory functionality and integrates with LiteLLM for a complete AI development environment.

## Deployment Options

You have two primary options for deploying Aithena Services:

1. **Complete Stack with Docker Compose** (recommended for most users)
2. **Standalone Memory Service** (for development or specific integration needs)

## Option 1: Complete Stack with Docker Compose

This option sets up the entire development environment including Ollama, LiteLLM, and Aithena Services.

### Prerequisites

- Docker and Docker Compose installed
- Git installed
- Basic understanding of terminal/command line

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-org/aithena-services.git
   cd aithena-services
   ```

2. **Configure Environment**:
   ```bash
   cp .env.sample .env
   # Edit .env with your settings (passwords, API keys)
   ```

3. **Start Services**:
   ```bash
   docker compose up -d
   ```

This will start the services, including the API server at port 8000 and LiteLLM at port 4000.

## Option 2: Standalone Memory Service

Use this option if you want to run Aithena Services directly on your machine.

### Prerequisites

- PostgreSQL with `pgvector` extension installed and running
- Python 3.11+
- `uv` or `pip` for package management

### Steps

1. **Clone and Install**:
   ```bash
   git clone https://github.com/your-org/aithena-services.git
   cd aithena-services
   pip install -e .
   ```

2. **Configure Environment**:
   Create a `.env` file with your database configuration:
   ```bash
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your-password
   POSTGRES_DB=aithena
   ```

3. **Start the Service**:
   You can use the installed CLI command:
   ```bash
   aithena-services serve --port 8000 --reload
   ```

## Using the Memory API

Example using Python requests:

```python
import requests

# Search for similar works
response = requests.post(
    "http://localhost:8000/memory/pgvector/search_works",
    json={
        "table_name": "openalex.abstract_embeddings_arctic",
        "vector": [0.1, 0.2, ...], # Your embedding vector
        "n": 5,
        "languages": ["en"],
        "start_year": 2023
    }
)

results = response.json()
print(results)
```

## Common Issues

- **"Relation does not exist"**: Ensure your PostgreSQL database has the required tables (e.g., `openalex.abstract_embeddings_arctic`) and the `vector` extension enabled.
- **Connection Refused**: Check if your PostgreSQL server is running and accessible at the host/port specified in `.env`.

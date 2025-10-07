# get-openalex 📚🔍

[![Version](https://img.shields.io/badge/version-0.1.0--dev1-blue.svg)](https://github.com/yourusername/get-openalex)
[![Python](https://img.shields.io/badge/python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.11%2B-ff69b4.svg)](https://fastapi.tiangolo.com/)

A powerful tool for accessing and processing [OpenAlex](https://openalex.org/) data through multiple interfaces.

> 🔥 **NEW**: API server with PostgreSQL integration for storing fetched data!

## 🚀 Features

This tool provides three main ways to access OpenAlex data:

1. **🪣 S3 Bucket Access**: Download OpenAlex data dumps directly from their S3 bucket
2. **🌐 REST API Client**: Query the OpenAlex REST API with convenient utilities for filtering, pagination, and data processing
3. **🖥️ API Server**: Run your own FastAPI server to provide an OpenAlex query interface with optional PostgreSQL storage

## 📦 Installation

```shell
# From the repository root after cloning
pip install .

# Or directly from a package repository (when published)
pip install get-openalex
```

## 🛠️ CLI Commands

### Main CLI Help

```shell
get-openalex --help
```

This shows all available commands including:
- `s3` subcommands for S3 bucket operations
- `search-works` to search for works using the REST API
- `version` to display the current version

### 🔍 REST API Operations

Search for works using the OpenAlex REST API:

```shell
# Basic search
get-openalex search-works --query "machine learning" --limit 20

# Search with date filter
get-openalex search-works --query "machine learning" --from-date "2023-01-01" --limit 20

# Search with author filter
get-openalex search-works --author-id "A123456789" --limit 20

# Search with multiple filters
get-openalex search-works --query "CRISPR" --from-date "2023-01-01" --concept-id "C123456789" --limit 20
```

#### Output Formats

Output formats supported:
- Text (default): `--format text`
- JSON: `--format json`
- CSV: `--format csv`

Examples:

```shell
# Export to JSON file
get-openalex search-works --query "CRISPR" --from-date "2023-01-01" --format json > crispr_papers.json

# Export to CSV file
get-openalex search-works --query "quantum computing" --from-date "2022-01-01" --format csv > quantum_papers.csv
```

### 🪣 S3 Operations

List what's available in the S3 bucket:

```shell
# List all available data types
get-openalex s3 list-available

# List available Author data from a specific date
get-openalex s3 list-available --type "Authors" --fromDate "2023-01-01"

# List available Works data (publications)
get-openalex s3 list-available --type "Works"
```

Download data from OpenAlex S3 bucket:

```shell
# Download all data types from a specific date
get-openalex s3 download --outDir "/path/to/output" --fromDate "2023-01-01"

# Download only Works data
get-openalex s3 download --outDir "/path/to/output" --fromDate "2023-01-01" --onlyType "Works"

# Download all Authors data (from all available dates)
get-openalex s3 download --outDir "/path/to/output" --onlyType "Authors"
```

You can also directly use the dedicated S3 CLI:

```shell
get-openalex-s3 download --outDir "/path/to/output" --fromDate "2023-01-01"
```

## 📊 S3 Parameters

### Required - outDir
`--outDir` or the environment variable `OUT_DIR` specifies the directory where the downloaded data will be stored.

### Optional - onlyType
You can specify if you want to download only data for a specific OpenAlex Object:

```shell
get-openalex s3 download --outDir "/path/to/output" --fromDate "2023-01-01" --onlyType "Authors"
```

This, for example, would download only Authors.
The value of `onlyType` must be a single string, one of:
- `Authors`
- `Works`
- `Venues`
- `Institutions`
- `Concepts`
- `Topics`
- `Publishers`
- `Sources`
- `Funders`

### fromDate - S3_FROM_DATE

`--fromDate` or the environment variable `S3_FROM_DATE` will specify the **first** day from when data will be downloaded.
If no date is specified and the value of environment variable `ALL_MONTH` is either not set or it is set to `False` or `0`, **all the data** will be downloaded.
The date must follow ISO8601 format, for example: "2024-11-28"

### env: ALL_LAST_MONTH

If `ALL_LAST_MONTH` is set to `True` or `1`, when `get-openalex` is executed, the value of `fromDate` will be the result of executing:

```python
from datetime import date
today_ = date.today()
from_date = today_.replace(day=1, month=today_.month-1).isoformat()
```
so all data starting from the first day of the current month will be downloaded.
This would mean that the job needs to be run on the first day of each month.

## 💻 Python API

You can use get-openalex as a Python library for both S3 and REST API operations:

### REST API Usage

The package provides convenient functions for interacting with the OpenAlex REST API:

```python
from polus.aithena.jobs.getopenalex import (
    get_filtered_works,
    get_filtered_works_dict,
    iter_filtered_works_cursor,
    WorksPaginator
)

# Simple query: Get works filtered by date (returns a list of work objects)
works = get_filtered_works({"from_publication_date": "2023-01-01"}, max_results=100)
print(f"Retrieved {len(works)} works")

# Search with a query term and multiple filters
works = get_filtered_works({
    "search": "machine learning",
    "from_publication_date": "2023-01-01",
    "author.id": "A123456789"
}, max_results=50)

# Get works as dictionaries instead of objects
works_dict = get_filtered_works_dict({"from_publication_date": "2023-01-01"}, max_results=100)

# Efficiently iterate through works using cursor-based pagination
# This is memory-efficient for large result sets
for work in iter_filtered_works_cursor({"from_publication_date": "2023-01-01"}):
    print(work.title)
    # Stop after processing 100 works
    if work.id.endswith("00"):
        break

# For more control over pagination
paginator = WorksPaginator(
    filters={"from_publication_date": "2023-01-01"},
    per_page=50
)

# Process pages of results
for page in paginator.iter_pages(max_pages=5):
    print(f"Page {paginator.current_page}: {len(page)} results")
    # Process each work in the page
    for work in page:
        print(work.title)

# Async usage for better performance
import asyncio

async def get_works_async():
    from polus.aithena.jobs.getopenalex import get_filtered_works_async
    
    works = await get_filtered_works_async(
        {"search": "quantum computing", "from_publication_date": "2023-01-01"},
        max_results=50
    )
    return works

# Run the async function
works = asyncio.run(get_works_async())
```

### Advanced REST API Features

```python
# Use the metrics collector to track API usage
from polus.aithena.jobs.getopenalex import metrics_collector

# Make API calls
works = get_filtered_works({"from_publication_date": "2023-01-01"}, max_results=100)

# Get metrics
print(f"API calls made: {metrics_collector.api_calls}")
print(f"Results retrieved: {metrics_collector.results_retrieved}")
print(f"Cache hits: {metrics_collector.cache_hits}")

# Use context managers for custom session handling
from polus.aithena.jobs.getopenalex import api_session

with api_session(timeout=30) as session:
    # Custom API operations with the session
    pass
```

### S3 API Usage

For S3 operations, you can use the s3_app directly:

```python
# Basic S3 download function
from polus.aithena.jobs.getopenalex import s3_app
from pathlib import Path

# Download all data from a specific date
s3_app.download(
    out_dir=Path("/path/to/output"),
    from_date="2023-01-01"
)

# Download specific data type
s3_app.download(
    out_dir=Path("/path/to/output"),
    from_date="2023-01-01",
    only_type="Works"
)

# List available data in S3
available_data = s3_app.list_available(data_type="Authors", from_date="2023-01-01")
print(available_data)

# Using the callback approach
s3_app.callback()(
    out_dir=Path("/path/to/output"), 
    from_date="2023-01-01", 
    only_type="Authors"
)
```

## 🖥️ API Server

You can run a FastAPI server that provides an interface to the OpenAlex API and optionally stores data in PostgreSQL:

### Environment Variables

Key environment variables for the API server:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | Host to bind the API server | `127.0.0.1` |
| `API_PORT` | Port for the API server | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PYALEX_EMAIL` | Email for OpenAlex API requests | `None` |
| `POSTGRES_URL` | PostgreSQL connection string | `None` |
| `USE_POSTGRES` | Whether to store data in PostgreSQL | `False` |
| `JOB_DATABASE_URL` | SQLite database for job tracking | `sqlite:///./openalex_jobs.db` |
| `UPDATE_BATCH_SIZE` | Batch size for update jobs | `100` |
| `UPDATE_MAX_RECORDS` | Maximum records per update job | `10000` |

### Starting the API Server

Running the server directly:

```shell
# Start the API server
python -m polus.aithena.jobs.getopenalex.api.run
```

### Docker Deployment

Using Docker Compose:

```shell
# Start in the background
docker-compose up -d

# Check logs
docker-compose logs -f
```

### API Endpoints

Key API endpoints:

- `GET /works?query=<query>&from_date=<YYYY-MM-DD>` - Search for works
- `GET /works/{work_id}` - Get a specific work by ID
- `GET /health` - Health check endpoint
- `GET /jobs` - List update jobs
- `POST /update` - Start a data update job

### PostgreSQL Integration (Optional)

The API server can store data in PostgreSQL for persistence. This feature is **optional** and can be disabled if you don't need data storage.

To enable PostgreSQL integration:

1. Set `USE_POSTGRES=True` in your `.env` file
2. Provide a valid `POSTGRES_URL` connection string

If PostgreSQL integration is disabled:
- The API will still function normally for queries
- Update jobs will still run and count records but won't store data
- All data will be fetched directly from OpenAlex on demand

Example of starting an update job without PostgreSQL:

```shell
# Start the API server with PostgreSQL disabled
export USE_POSTGRES=False
python -m polus.aithena.jobs.getopenalex.api.run
```

Or via the API:

```bash
curl -X POST "http://localhost:8000/update" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "WORKS_UPDATE", 
    "from_date": "2023-01-01", 
    "max_records": 1000,
    "use_postgres": false
  }'
```

## 🖥️ FastAPI Server

get-openalex includes a FastAPI server that provides a web API for querying OpenAlex data. This allows you to create a service that other applications can use to search and retrieve OpenAlex works.

> ℹ️ **NOTE**: The API server can store fetched data in a PostgreSQL database if configured.

### Running the API Server

To run the API server:

```shell
# Using the CLI command (basic)
get-openalex serve

# With custom host and port
get-openalex serve --host 0.0.0.0 --port 8000 

# With auto-reload for development
get-openalex serve --host 0.0.0.0 --port 8000 --reload

# Or directly with Python
python -m polus.aithena.jobs.getopenalex.api.run --host 0.0.0.0 --port 8000
```

### Environment Variables for API Server

```
# Core settings
API_HOST=0.0.0.0  # Host to bind the API server to
API_PORT=8000     # Port for the API server
LOG_LEVEL=INFO    # Logging level (DEBUG, INFO, WARNING, ERROR)

# Optional PostgreSQL connection (if you want to store fetched data)
POSTGRES_URL=postgresql://username:password@hostname:5432/database

# Update job settings (for PostgreSQL storage feature)
UPDATE_BATCH_SIZE=100    # Number of records per batch
UPDATE_MAX_RECORDS=10000 # Max records per job

# Job database path (for job tracking)
JOB_DATABASE_URL=sqlite:///./openalex_jobs.db
```

### API Endpoints

Once running, the API provides the following endpoints:

- `GET /works` - Search for works with query parameters
- `POST /works/search` - Search for works with a JSON request body
- `GET /works/{work_id}` - Get a specific work by ID
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

If PostgreSQL integration is enabled:
- `POST /update` - Start a database update job
- `GET /jobs` - List update jobs
- `GET /jobs/{job_id}` - Get job details
- `GET /jobs/{job_id}/logs` - Get job logs

### Example API Requests

```shell
# Health check
curl "http://localhost:8000/health"

# Search for works via GET request
curl "http://localhost:8000/works?query=machine+learning&from_date=2023-01-01&limit=5"

# Search for works via POST request
curl -X POST "http://localhost:8000/works/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "from_date": "2023-01-01", "limit": 5}'

# Get a specific work by ID
curl "http://localhost:8000/works/W2741809807"

# Start a database update job (if PostgreSQL is configured)
curl -X POST "http://localhost:8000/update" \
  -H "Content-Type: application/json" \
  -d '{"job_type": "WORKS_UPDATE", "from_date": "2023-01-01"}'
```

### API Documentation

Detailed API documentation is available at `/docs` when the server is running:

```
http://localhost:8000/docs
```

## 🐳 Docker 

### Basic S3 Operations

```shell
# Download data from S3
docker run -v ${DATA_DIR}:/outDir ${DOCKER_ORG}/get-openalex:${VERSION} s3 download --fromDate 2024-01-01 --outDir=/outDir

# Download specific data type
docker run -v ${DATA_DIR}:/outDir ${DOCKER_ORG}/get-openalex:${VERSION} s3 download --fromDate 2024-01-01 --outDir=/outDir --onlyType Authors 

# List available data
docker run ${DOCKER_ORG}/get-openalex:${VERSION} s3 list-available --type Works
```

### Running the API Server in Docker

```shell
# Basic API server
docker run -p 8000:8000 ${DOCKER_ORG}/get-openalex:${VERSION} get-openalex serve --host 0.0.0.0 --port 8000

# With volume for SQLite database persistence
docker run -p 8000:8000 -v ${DATA_DIR}:/app/data ${DOCKER_ORG}/get-openalex:${VERSION} get-openalex serve --host 0.0.0.0 --port 8000

# With PostgreSQL integration (optional)
docker run -p 8000:8000 \
  -e POSTGRES_URL=postgresql://username:password@hostname:5432/database \
  ${DOCKER_ORG}/get-openalex:${VERSION} get-openalex serve --host 0.0.0.0 --port 8000
```

For more detailed Docker documentation, see [DOCKER.md](DOCKER.md)

## ⚓ Helm 

For Kubernetes deployment, a Helm chart is included:

```shell
cd helm
```

Make sure to update `values.yaml` to match your environment. In particular, the `persistentVolume:hostPath` entry.

```shell
# Create namespace
kubectl create namespace job

# Install chart
helm install getoa . -n job

# For microk8s
microk8s kubectl create namespace job
microk8s helm install getoa . -n job
```

## 📚 Documentation

For more detailed documentation, see the [docs](docs) directory:

- [API Reference](docs/api_reference.md) - Detailed API endpoint documentation
- [Database Updates](docs/database_updates.md) - Guide to using the PostgreSQL integration (optional)
- [Technical Details](docs/technical_details.md) - Details about the database models and logging
- [Environment Variables](docs/environment_variables.md) - Complete reference for all configuration options

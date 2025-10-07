# Environment Variables

This document provides a comprehensive overview of all environment variables used in the get-openalex package. Environment variables are used for configuration across different components of the system, including the CLI tools, API server, and database connections.

## Core Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Controls verbosity of logs. |

## S3 Operation Variables

These variables control the behavior of the S3 download functionality:

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_OUT_DIR` | None (Required) | Directory where downloaded OpenAlex data will be stored. This is a required parameter for S3 download operations. |
| `S3_FROM_DATE` | None | First day to download data from (ISO8601 format, e.g., "2023-01-01"). If not specified and `ALL_MONTH` is not set, all available data will be downloaded. |
| `ALL_MONTH` | `False` | When set to `True` or `1`, downloads all data for a specific month (requires `S3_FROM_DATE` to be set). |
| `ALL_LAST_MONTH` | `False` | When set to `True` or `1`, automatically sets `S3_FROM_DATE` to the first day of the previous month, downloading all data since then. Useful for monthly updates. |

## API Server Variables

These variables control the behavior of the FastAPI server:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `127.0.0.1` | Host to bind the API server to. Use `0.0.0.0` to accept connections from any IP address. |
| `API_PORT` | `8000` | Port for the API server to listen on. |

## Database Connection Variables

These variables control database connections for both the job tracking database and the OpenAlex data storage:

| Variable | Default | Description |
|----------|---------|-------------|
| `JOB_DATABASE_URL` | `sqlite:///./openalex_jobs.db` | SQLAlchemy connection string for the job tracking database. Can be SQLite, PostgreSQL, or any other database supported by SQLAlchemy. |
| `POSTGRES_URL` | None | PostgreSQL connection string for storing OpenAlex data (e.g., `postgresql://username:password@hostname:5432/database`). Required if you want to store OpenAlex data in a database. |

## Update Job Control Variables

These variables control the behavior of database update jobs:

| Variable | Default | Description |
|----------|---------|-------------|
| `UPDATE_BATCH_SIZE` | `100` | Number of records to process per batch when updating the database. Adjust based on available memory and database performance. |
| `UPDATE_MAX_RECORDS` | `10000` | Maximum number of records to process in a single update job. Set to `-1` for no limit. |

## API Request Configuration

These variables control API request behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENALEX_API_KEY` | None | API key for the OpenAlex API. Not required, but helps avoid rate limiting if you have one. |
| `API_REQUEST_TIMEOUT` | `30` | Default timeout for API requests in seconds. |
| `API_MAX_RETRIES` | `3` | Maximum number of retries for failed API requests. |

## Using Environment Variables

### Command Line

You can set environment variables when running commands:

```bash
# Set the S3_OUT_DIR environment variable for a single command
S3_OUT_DIR=/path/to/data get-openalex s3 download --fromDate 2023-01-01

# Set multiple variables
S3_OUT_DIR=/path/to/data S3_FROM_DATE=2023-01-01 get-openalex s3 download
```

### Environment File (.env)

For convenience, you can create a `.env` file in your project directory:

```
# .env file example
S3_OUT_DIR=/path/to/data
S3_FROM_DATE=2023-01-01
POSTGRES_URL=postgresql://username:password@hostname:5432/database
JOB_DATABASE_URL=sqlite:///./jobs.db
API_HOST=0.0.0.0
API_PORT=8080
UPDATE_BATCH_SIZE=200
UPDATE_MAX_RECORDS=20000
OPENALEX_API_KEY=your_api_key_here
```

The package will automatically load these variables if python-dotenv is installed.

### Docker

When using Docker, you can pass environment variables using the `-e` flag:

```bash
docker run -e S3_OUT_DIR=/outDir -e S3_FROM_DATE=2023-01-01 -v ${DATA_DIR}:/outDir ${DOCKER_ORG}/get-openalex:${VERSION} s3 download
```

Or using a docker-compose.yml file:

```yaml
version: '3'
services:
  get-openalex:
    image: ${DOCKER_ORG}/get-openalex:${VERSION}
    environment:
      - S3_OUT_DIR=/outDir
      - S3_FROM_DATE=2023-01-01
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - POSTGRES_URL=postgresql://username:password@postgres:5432/openalex
      - UPDATE_BATCH_SIZE=200
      - UPDATE_MAX_RECORDS=20000
      - OPENALEX_API_KEY=your_api_key_here
    volumes:
      - ${DATA_DIR}:/outDir
```

## Priority Order

Environment variables are evaluated in the following order (highest priority first):

1. Command-line arguments (when available)
2. Environment variables set in the shell or passed to the container
3. Values from .env file
4. Default values hard-coded in the application

This means command-line arguments will always override environment variables, which in turn override defaults. 
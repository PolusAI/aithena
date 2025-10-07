# Docker Setup for OpenAlex API

This guide explains how to run the OpenAlex API using Docker Compose.

## Architecture

The system consists of:

1. **OpenAlex API Service** - Fetches data from the OpenAlex REST API
2. **SQLite Database** - Used for job tracking metadata (containerized with the API)
3. **Optional PostgreSQL Integration** - If desired, the fetched data can be stored in a PostgreSQL database

> **Note**: Using PostgreSQL is completely optional. The API can fetch and process data from OpenAlex without storing it in a database.

## Getting Started

### Prerequisites

- Docker and Docker Compose installed (Docker Compose V2)
- If using the PostgreSQL feature: network access from the Docker container to your PostgreSQL server

### Quick Start

1. Configure environment variables:

   ```bash
   cp .env.sample .env
   ```

   Edit the `.env` file to configure your setup:

   ```
   # If using the PostgreSQL feature, configure your connection:
   POSTGRES_URL=postgresql://username:password@your-postgres-host:5432/openalex
   ```

   > **Note**: If PostgreSQL is running on the Docker host, use `host.docker.internal` as the hostname.

2. Start the API service:

   ```bash
   docker compose up -d
   ```

3. Check that the service is running:

   ```bash
   docker compose ps
   ```

4. Run your first update with a specific date:

   ```bash
   ./daily-update.sh 2024-02-01
   ```

5. Set up daily updates (in crontab):

   ```bash
   # Add to crontab
   0 2 * * * /path/to/daily-update.sh
   ```

## Volume Structure

- `sqlite_data`: Stores the SQLite job tracking database
- `logs`: Stores application logs

## Environment Variables

Configure these in your `.env` file:

### Optional Database Connection

- `POSTGRES_URL`: PostgreSQL connection string (for storing fetched data)
  - Format: `postgresql://username:password@hostname:5432/database`
  - Default fallback: `postgresql://postgres:postgres@host.docker.internal:5432/openalex`
  - **Note**: This is only needed if you want to store data in PostgreSQL

### API Configuration

- `API_PORT`: Port to expose the API on the host (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

### Update Job Configuration

- `UPDATE_BATCH_SIZE`: Number of records per batch (default: 100)
- `UPDATE_MAX_RECORDS`: Maximum records per job (default: 10000)

## Monitoring and Management

### View Logs

```bash
# View API logs
docker compose logs -f openalex-api
```

### Check Job Status

```bash
# List recent jobs
curl http://localhost:8000/jobs

# Get specific job details
curl http://localhost:8000/jobs/123

# Get job logs
curl http://localhost:8000/jobs/123/logs
```

### SQLite Database Backup

The job tracking database is stored in a Docker volume. To create a backup:

```bash
# Backup SQLite job database
docker cp openalex-api:/app/data/openalex_jobs.db ./job_backup.db
```

## Troubleshooting

### API Not Responding

Check if the container is running:

```bash
docker compose ps
```

Check the logs:

```bash
docker compose logs openalex-api
```

Restart the service:

```bash
docker compose restart openalex-api
```

### PostgreSQL Connection Issues (If Using This Feature)

If you're using the optional PostgreSQL feature and the API can't connect to your PostgreSQL database, check:

1. Network access - Can the container reach your PostgreSQL server?
2. Credentials - Are the username and password correct?
3. Database exists - Does the specified database exist?
4. PostgreSQL configuration - Is PostgreSQL configured to accept remote connections?

Test the connection from inside the container:

```bash
docker exec -it openalex-api bash
python -c "import psycopg2; conn = psycopg2.connect('$POSTGRES_URL'); print('Connection successful')"
```

### View SQLite Database Content

```bash
docker exec -it openalex-api bash
sqlite3 /app/data/openalex_jobs.db
.tables
SELECT * FROM job ORDER BY created_at DESC LIMIT 5;
.exit
``` 
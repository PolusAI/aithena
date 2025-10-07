# 📚 OpenAlex API Documentation

Welcome to the documentation for the OpenAlex API and Data Access System.

## 📋 Documentation Overview

This documentation provides comprehensive information about the OpenAlex API system, which allows you to:

1. 🔍 Query the OpenAlex API through a REST interface
2. 💾 Optionally store fetched data in a PostgreSQL database 
3. 📊 Track and monitor API usage and update jobs
4. ⏱️ Set up automated daily updates

## 📑 Available Documentation

| Document | Description |
|----------|-------------|
| [Database Updates](database_updates.md) | How to use the optional PostgreSQL integration for storing OpenAlex data |
| [API Reference](api_reference.md) | Comprehensive reference for all API endpoints |
| [Technical Details](technical_details.md) | In-depth technical information about models, logging, and implementation details |

## 🚀 Quick Start

### Querying the OpenAlex API

Get recent machine learning papers:
```bash
curl "http://localhost:8000/works?query=machine%20learning&from_date=2023-01-01&limit=10"
```

Get a specific work by ID:
```bash
curl "http://localhost:8000/works/W12345"
```

### Setting Up Database Updates (Optional PostgreSQL Feature)

> **Note**: Storing data in PostgreSQL is completely optional. The API can fetch and process data from OpenAlex without storing it in a database.

If you've configured PostgreSQL integration:

1. First, perform an initial update with a specific start date:
   ```bash
   curl -X POST "http://localhost:8000/update" \
        -H "Content-Type: application/json" \
        -d '{"job_type": "WORKS_UPDATE", "from_date": "2024-01-01"}'
   ```

2. Set up a daily cron job to run:
   ```bash
   0 2 * * * curl -X POST "http://localhost:8000/update" \
        -H "Content-Type: application/json" \
        -d '{"job_type": "WORKS_UPDATE"}'
   ```

3. Monitor job status:
   ```bash
   curl "http://localhost:8000/jobs"
   ```

4. View job logs:
   ```bash
   curl "http://localhost:8000/jobs/123/logs"
   ```

## ⚙️ Configuration

The system can be configured using environment variables:

### Core API Settings
- `API_HOST`: Host to bind the API server (default: `127.0.0.1`)
- `API_PORT`: Port for the API server (default: `8000`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `JOB_DATABASE_URL`: SQLite database path for job tracking (default: `sqlite:///./openalex_jobs.db`)

### Optional PostgreSQL Integration
- `POSTGRES_URL`: PostgreSQL connection string *(only needed if using PostgreSQL storage)*
- `UPDATE_BATCH_SIZE`: Number of records to process in a batch (default: `100`)
- `UPDATE_MAX_RECORDS`: Maximum number of records to process per job (default: `10000`)

## 🔗 Related Resources

- [OpenAlex Documentation](https://docs.openalex.org/) - Official OpenAlex API documentation
- [OpenAlex Entity Schema](https://docs.openalex.org/api-entities/works) - Schema information for OpenAlex entities

See the individual documentation files for more detailed information. 
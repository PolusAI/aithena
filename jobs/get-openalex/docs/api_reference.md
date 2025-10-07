# 🌐 OpenAlex API Reference

This document provides a comprehensive reference for the OpenAlex API endpoints.

## 📋 Table of Contents
- [OpenAlex Data Access Endpoints](#openalex-data-access-endpoints)
  - [GET /works](#get-works)
  - [POST /works/search](#post-workssearch)
  - [GET /works/{work_id}](#get-workswork_id)
- [Job Management Endpoints](#job-management-endpoints-for-postgresql-integration)
(For PostgreSQL Integration)
  - [GET /jobs](#get-jobs)
  - [GET /jobs/{job_id}](#get-jobsjob_id)
  - [GET /jobs/{job_id}/logs](#get-jobsjob_idlogs)
- [Database Update Endpoints](#database-update-endpoints-for-postgresql-integration) (For PostgreSQL Integration)
  - [POST /update](#post-update)
  - [Utility Endpoints](#utility-endpoints)
  - [GET /health](#get-health)
  - [GET /](#get-)

## 🔍 OpenAlex Data Access Endpoints

> These endpoints retrieve data directly from the OpenAlex REST API and are always available, regardless of whether you use the optional PostgreSQL integration.

### GET /works

Retrieves a list of works from OpenAlex with support for various filters and pagination.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | Search query |
| from_date | string | Filter works published after this date (YYYY-MM-DD) |
| to_date | string | Filter works published before this date (YYYY-MM-DD) |
| author_id | string | Filter by author ID |
| institution_id | string | Filter by institution ID |
| venue_id | string | Filter by venue ID |
| concept_id | string | Filter by concept ID |
| page | integer | Page number (default: 1) |
| per_page | integer | Results per page (default: 10, max: 100) |
| limit | integer | Maximum number of results (default: 50, max: 200) |

#### Example Request

```bash
curl "http://localhost:8000/works?query=machine%20learning&from_date=2023-01-01&page=1&per_page=10"
```

#### Response

```json
{
  "count": 150,
  "next_page": 2,
  "prev_page": null,
  "current_page": 1,
  "total_pages": 15,
  "results": [
    {
      "id": "https://openalex.org/W12345",
      "title": "Example Machine Learning Paper",
      "publication_date": "2023-02-15",
      "doi": "10.1234/example",
      "abstract": "This is an example abstract...",
      ...
    },
    ...
  ]
}
```

### POST /works/search

Similar to GET /works but accepts a request body for more complex queries.

#### Request Body

```json
{
  "query": "machine learning",
  "from_date": "2023-01-01",
  "to_date": "2023-12-31",
  "author_id": "A12345",
  "institution_id": null,
  "venue_id": null,
  "concept_id": null,
  "page": 1,
  "per_page": 10,
  "limit": 50
}
```

#### Example Request

```bash
curl -X POST "http://localhost:8000/works/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "machine learning", "from_date": "2023-01-01"}'
```

#### Response

Same format as GET /works.

### GET /works/{work_id}

Retrieves a specific work by its ID.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| work_id | string | OpenAlex work ID (with or without the prefix) |

#### Example Request

```bash
curl "http://localhost:8000/works/W12345"
```

#### Response

```json
{
  "id": "https://openalex.org/W12345",
  "title": "Example Paper",
  "publication_date": "2023-02-15",
  "doi": "10.1234/example",
  ...
}
```

## Job Management Endpoints (For PostgreSQL Integration)

> **Note**: These endpoints are only relevant if you've configured the optional PostgreSQL integration. They allow you to monitor and manage database update jobs.

### GET /jobs

Retrieves a list of database update jobs that have been run to populate your PostgreSQL database.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by job status (PENDING, RUNNING, COMPLETED, FAILED, ABORTED) |
| job_type | string | Filter by job type (WORKS_UPDATE, AUTHORS_UPDATE, etc.) |
| limit | integer | Maximum number of jobs to return (default: 10, max: 100) |

#### Example Request

```bash
curl "http://localhost:8000/jobs?status=COMPLETED&limit=5"
```

#### Response

```json
[
  {
    "id": 123,
    "job_type": "WORKS_UPDATE",
    "status": "COMPLETED",
    "created_at": "2023-06-15T10:30:00Z",
    "started_at": "2023-06-15T10:30:05Z",
    "completed_at": "2023-06-15T10:45:20Z",
    "records_processed": 5000,
    "records_created": 4500,
    "records_updated": 500,
    "records_failed": 0,
    "parameters": {
      "from_date": "2023-06-01"
    },
    "error_message": null,
    "duration_seconds": 915
  },
  ...
]
```

### GET /jobs/{job_id}

Retrieves details about a specific job.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | integer | Job ID |

#### Example Request

```bash
curl "http://localhost:8000/jobs/123"
```

#### Response

Same format as a single job in the GET /jobs response.

### GET /jobs/{job_id}/logs

Retrieves logs for a specific job.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | integer | Job ID |

#### Example Request

```bash
curl "http://localhost:8000/jobs/123/logs"
```

#### Response

```json
[
  {
    "id": 1,
    "job_id": 123,
    "timestamp": "2023-06-15T10:30:05Z",
    "level": "INFO",
    "message": "Starting works update from 2023-06-01",
    "details": {
      "from_date": "2023-06-01"
    }
  },
  {
    "id": 2,
    "job_id": 123,
    "timestamp": "2023-06-15T10:35:10Z",
    "level": "INFO",
    "message": "Job progress: 2500",
    "details": {
      "progress_current": 2500,
      "created": 2300,
      "updated": 200
    }
  },
  ...
]
```

## Database Update Endpoints (For PostgreSQL Integration)

> **Note**: These endpoints are only relevant if you've configured the optional PostgreSQL integration. They allow you to manage the storage of OpenAlex data in your PostgreSQL database.

### POST /update

Starts a new database update job to fetch data from OpenAlex and store it in your PostgreSQL database.

#### Prerequisites

- PostgreSQL must be configured via the `POSTGRES_URL` environment variable
- The OpenAlex API service must be running

#### Request Body

```json
{
  "job_type": "WORKS_UPDATE",
  "from_date": "2023-01-01",
  "max_records": 10000
}
```

| Field | Type | Description |
|-------|------|-------------|
| job_type | string | Type of update job (currently only WORKS_UPDATE is supported) |
| from_date | string | Optional. Start date for updates (YYYY-MM-DD) |
| max_records | integer | Optional. Maximum number of records to process |

#### Example Request

```bash
curl -X POST "http://localhost:8000/update" \
     -H "Content-Type: application/json" \
     -d '{"job_type": "WORKS_UPDATE", "from_date": "2023-01-01"}'
```

#### Response

```json
{
  "id": 124,
  "job_type": "WORKS_UPDATE",
  "status": "PENDING",
  "created_at": "2023-06-16T09:00:00Z",
  "started_at": null,
  "completed_at": null,
  "records_processed": 0,
  "records_created": 0,
  "records_updated": 0,
  "records_failed": 0,
  "parameters": {
    "from_date": "2023-01-01"
  },
  "error_message": null,
  "duration_seconds": null
}
```

## Utility Endpoints

### GET /health

Health check endpoint.

#### Example Request

```bash
curl "http://localhost:8000/health"
```

#### Response

```json
{
  "status": "ok"
}
```

### GET /

API root endpoint that lists available endpoints.

#### Example Request

```bash
curl "http://localhost:8000/"
```

#### Response

```json
{
  "name": "OpenAlex API",
  "version": "0.1.0",
  "description": "API for querying OpenAlex academic data and managing database updates",
  "endpoints": [
    "/works",
    "/works/search",
    "/works/{work_id}",
    "/health",
    "/jobs",
    "/jobs/{job_id}",
    "/jobs/{job_id}/logs",
    "/update",
    "/docs"
  ]
}
``` 
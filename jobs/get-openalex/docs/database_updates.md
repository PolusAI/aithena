# 🗄️ OpenAlex Database Integration (Optional)

This document explains how to use the optional PostgreSQL integration for storing OpenAlex data retrieved from the API.

> **Note**: This PostgreSQL integration is completely optional. The OpenAlex API service works without a database, directly fetching data from the OpenAlex REST API as needed. The database integration is for users who want to maintain a local copy of the data.

## 📋 Table of Contents
- [Overview](#overview)
- [Initial Setup](#initial-setup)
- [Daily Updates](#daily-updates)
- [How Incremental Updates Work](#how-incremental-updates-work)
- [Monitoring Jobs](#monitoring-jobs)
- [Troubleshooting](#troubleshooting)

## 📝 Overview

The optional OpenAlex database integration provides functionality to:

1. Store data fetched from the OpenAlex API in your PostgreSQL database
2. Perform efficient incremental updates based on modification date
3. Track job progress, status, and statistics
4. Handle errors gracefully and provide detailed logs

The system is designed to run as a background process triggered via a REST API endpoint, making it ideal for containerized environments like Kubernetes.

## 🚀 Initial Setup

### Prerequisites

1. A PostgreSQL database server
2. The OpenAlex API service running
3. Configure the `POSTGRES_URL` environment variable with your PostgreSQL connection string

### Configuration

Set up your PostgreSQL connection in the environment variables:

```bash
# Example PostgreSQL connection string
export POSTGRES_URL="postgresql://username:password@hostname:5432/database"
```

You can also set these variables in your `.env` file or Docker configuration.

### First-Time Update

If you're starting with a database that already has data up to a certain date (e.g., 2024-01-31), you'll want to explicitly specify this date for your first update:

```bash
curl -X POST "http://localhost:8000/update" \
     -H "Content-Type: application/json" \
     -d '{"job_type": "WORKS_UPDATE", "from_date": "2024-02-01"}'
```

This will fetch all OpenAlex records created or updated since February 1, 2024.

If you're starting with an empty database:

```bash
curl -X POST "http://localhost:8000/update" \
     -H "Content-Type: application/json" \
     -d '{"job_type": "WORKS_UPDATE", "from_date": "2023-01-01"}'
```

Choose a reasonable start date based on your needs. The farther back, the longer the initial update will take.

### Configuration Options

You can configure the update process using environment variables:

- `POSTGRES_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/openalex`)
- `UPDATE_BATCH_SIZE`: Number of records to process in a batch (default: 100)
- `UPDATE_MAX_RECORDS`: Maximum number of records to process per job (default: 10000)

## Daily Updates

After the initial setup, you'll want to run daily updates to keep your database in sync with OpenAlex.

### API Call

For daily updates, use the following API call:

```bash
curl -X POST "http://localhost:8000/update" \
     -H "Content-Type: application/json" \
     -d '{"job_type": "WORKS_UPDATE"}'
```

Notice that we **omit the `from_date` parameter**. This lets the system automatically determine the correct date based on your last successful update.

### Setting Up Cron Jobs

#### Standard Cron

To run the update daily at 2:00 AM:

```bash
0 2 * * * curl -X POST "http://localhost:8000/update" -H "Content-Type: application/json" -d '{"job_type": "WORKS_UPDATE"}'
```

#### Kubernetes CronJob

If you're running in Kubernetes:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: openalex-daily-update
spec:
  schedule: "0 2 * * *"  # Run at 2:00 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: curl
            image: curlimages/curl:7.88.1
            command:
            - /bin/sh
            - -c
            - >
              curl -X POST "http://openalex-api-service:8000/update" 
              -H "Content-Type: application/json" 
              -d '{"job_type": "WORKS_UPDATE"}'
          restartPolicy: OnFailure
```

Replace `openalex-api-service` with your actual service name.

## How Incremental Updates Work

The system uses a sophisticated approach to only fetch records that have changed since your last update:

1. When no `from_date` is specified, the `_get_last_update_date()` method in `OpenAlexDBUpdater` is called
2. This method finds the date of the last successful update job from the job history database
3. If no previous job exists, it defaults to 7 days ago
4. OpenAlex API is then queried with `from_updated_date` filter to only fetch works updated since this date
5. For each record, the system checks if it exists in your database:
   - If it exists, the record is updated
   - If it doesn't exist, a new record is created
6. Job statistics (records processed, created, updated, failed) are tracked and saved

This approach ensures minimum data transfer and processing, making daily updates efficient.

## Monitoring Jobs

The API provides several endpoints to monitor update jobs:

### List Recent Jobs

```bash
curl "http://localhost:8000/jobs"
```

### Get Job Details

```bash
curl "http://localhost:8000/jobs/{job_id}"
```

### Get Job Logs

```bash
curl "http://localhost:8000/jobs/{job_id}/logs"
```

### Filter Jobs by Status or Type

```bash
curl "http://localhost:8000/jobs?status=COMPLETED"
curl "http://localhost:8000/jobs?job_type=WORKS_UPDATE"
```

## Troubleshooting

### Common Issues

1. **Job starts but fails quickly**
   - Check database connection string
   - Verify PostgreSQL is running
   - Look at job logs for specific error messages

2. **Job runs but processes 0 records**
   - Verify from_date isn't set to a future date
   - Check OpenAlex API status and rate limits
   - Ensure filters aren't too restrictive

3. **Job seems stuck**
   - Check if it's still running (status = RUNNING)
   - Look for progress in job logs
   - Consider setting a lower `UPDATE_MAX_RECORDS` limit

### Viewing Logs

The system uses structured JSON logging that works well with Kubernetes and other container orchestration platforms. Logs include job IDs, making it easy to filter for specific jobs.

In a containerized environment, you can view logs with:

```bash
kubectl logs -l app=openalex-api -c api
```

### Restarting Failed Jobs

If a job fails, you can start a new one with the same parameters:

```bash
curl -X POST "http://localhost:8000/update" \
     -H "Content-Type: application/json" \
     -d '{"job_type": "WORKS_UPDATE", "from_date": "2024-02-01"}'
```

Use the `from_date` from the failed job to continue from where it left off. 
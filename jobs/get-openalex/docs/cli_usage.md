# OpenAlex CLI Usage Guide

The `get-openalex` CLI provides commands for managing OpenAlex data synchronization, running update jobs, and monitoring job status.

## Installation

```bash
# Install with pip
pip install -e .

# Or with uv
uv pip install -e .
```

## Available Commands

### 📊 `update` - Run Data Update Job

Fetches updated works from the OpenAlex API and optionally stores them in PostgreSQL.

```bash
get-openalex update [OPTIONS]
```

**Options:**
- `--from-date, -f DATE`: Start date for updates (YYYY-MM-DD). If not provided, uses last successful update or 7 days ago.
- `--max-records, -m INT`: Maximum number of records to process. Default from config or 10000.
- `--use-postgres/--no-postgres`: Whether to store data in PostgreSQL. Default from config.
- `--dry-run`: Run without actually storing data, just count records.

**Examples:**

```bash
# Update from last successful run
get-openalex update

# Update from specific date
get-openalex update --from-date 2025-01-01

# Update with limited records (useful for testing)
get-openalex update --max-records 100

# Count records without storing (dry run)
get-openalex update --dry-run

# Update from date with PostgreSQL disabled
get-openalex update --from-date 2025-01-01 --no-postgres
```

**Output Example:**
```
[green]Starting OpenAlex update job...[/green]
  From date: 2025-01-01
  Max records: 100
  PostgreSQL storage: enabled

[green]Update job completed![/green]
  Job ID: 1
  Status: COMPLETED
  Records processed: 100
  Records created: 85
  Records updated: 15
  Records failed: 0
  Duration: 45.23 seconds
```

### 📋 `jobs` - List Update Jobs

Display recent update jobs with their status and statistics.

```bash
get-openalex jobs [OPTIONS]
```

**Options:**
- `--limit, -l INT`: Number of jobs to display (default: 10)
- `--status, -s TEXT`: Filter by job status (PENDING, RUNNING, COMPLETED, FAILED, ABORTED)
- `--type, -t TEXT`: Filter by job type (WORKS_UPDATE, AUTHORS_UPDATE, etc.)

**Examples:**

```bash
# Show last 10 jobs
get-openalex jobs

# Show last 20 jobs
get-openalex jobs --limit 20

# Show only failed jobs
get-openalex jobs --status FAILED

# Show only works update jobs
get-openalex jobs --type WORKS_UPDATE

# Show last 50 completed jobs
get-openalex jobs --status COMPLETED --limit 50
```

**Output Example:**
```
                    OpenAlex Update Jobs
┏━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ ID ┃ Type          ┃ Status    ┃ Started         ┃ Duration ┃ Processed ┃ Success Rate┃
┡━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 5  │ WORKS_UPDATE  │ COMPLETED │ 2025-01-11 15:20│ 120.5s   │ 5000      │ 99.8%       │
│ 4  │ WORKS_UPDATE  │ COMPLETED │ 2025-01-11 14:00│ 95.3s    │ 3500      │ 100.0%      │
│ 3  │ WORKS_UPDATE  │ FAILED    │ 2025-01-11 12:30│ 45.2s    │ 1200      │ 95.0%       │
│ 2  │ WORKS_UPDATE  │ COMPLETED │ 2025-01-10 15:00│ 200.7s   │ 10000     │ 99.9%       │
│ 1  │ WORKS_UPDATE  │ COMPLETED │ 2025-01-10 14:00│ 180.3s   │ 8500      │ 100.0%      │
└────┴───────────────┴───────────┴─────────────────┴──────────┴───────────┴─────────────┘
```

### 🚀 `serve` - Start API Server

Launch the FastAPI server for REST API access.

```bash
get-openalex serve [OPTIONS]
```

**Options:**
- `--host TEXT`: Host to bind the API server to (default: 127.0.0.1)
- `--port INT`: Port for the API server (default: 8000)
- `--reload`: Enable auto-reload for development

**Examples:**

```bash
# Start server with defaults
get-openalex serve

# Start on all interfaces
get-openalex serve --host 0.0.0.0

# Start on custom port
get-openalex serve --port 8080

# Development mode with auto-reload
get-openalex serve --reload
```

### 🔍 `search` - Search Works

Search for works using the OpenAlex API (REST API endpoint).

```bash
get-openalex search [OPTIONS] QUERY
```

**Options:**
- `--limit INT`: Maximum number of results (default: 10)

**Examples:**

```bash
# Search for machine learning papers
get-openalex search "machine learning"

# Search with limit
get-openalex search "covid-19" --limit 20
```

### 📦 `s3` - S3 Snapshot Operations

Manage OpenAlex S3 snapshots (subcommands).

```bash
get-openalex s3 [COMMAND] [OPTIONS]
```

**Subcommands:**
- `download`: Download snapshots from S3
- `process`: Process downloaded snapshots
- `list`: List available snapshots

### ℹ️ `version` - Display Version

Show the current version of get-openalex.

```bash
get-openalex version
```

## Environment Variables

The CLI respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PYALEX_EMAIL` | Email for OpenAlex API (required) | - |
| `OPENALEX_API_KEY` | API key for higher rate limits | - |
| `JOB_DATABASE_URL` | Job tracking database URL | sqlite:///openalex_jobs.db |
| `POSTGRES_URL` | PostgreSQL URL for data storage | - |
| `USE_POSTGRES` | Enable PostgreSQL storage | false |
| `UPDATE_BATCH_SIZE` | Batch size for updates | 100 |
| `UPDATE_MAX_RECORDS` | Default max records per update | 10000 |
| `LOG_LEVEL` | Logging level | INFO |

## Configuration File

You can also use a `.env` file in your working directory:

```bash
# .env file
PYALEX_EMAIL=your-email@example.com
OPENALEX_API_KEY=your-api-key
USE_POSTGRES=true
POSTGRES_URL=postgresql://user:pass@localhost/openalex
UPDATE_MAX_RECORDS=50000
LOG_LEVEL=DEBUG
```

## Daily Update Automation

### Using Cron (Linux/macOS)

Add to your crontab (`crontab -e`):

```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/get-openalex update >> /var/log/openalex-update.log 2>&1

# Run every 6 hours with limited records
0 */6 * * * /usr/local/bin/get-openalex update --max-records 10000
```

### Using systemd Timer (Linux)

Create `/etc/systemd/system/openalex-update.service`:

```ini
[Unit]
Description=OpenAlex Daily Update
After=network.target

[Service]
Type=oneshot
User=youruser
ExecStart=/usr/local/bin/get-openalex update
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/openalex-update.timer`:

```ini
[Unit]
Description=Run OpenAlex Update Daily
Requires=openalex-update.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:
```bash
sudo systemctl enable --now openalex-update.timer
```

### Using Task Scheduler (Windows)

Create a batch file `openalex-update.bat`:

```batch
@echo off
C:\Python\Scripts\get-openalex.exe update >> C:\logs\openalex-update.log 2>&1
```

Schedule it using Task Scheduler to run daily.

## Troubleshooting

### Common Issues

1. **"PYALEX_EMAIL not set"**
   - Set the environment variable: `export PYALEX_EMAIL=your-email@example.com`
   - Or add to `.env` file

2. **Rate limiting errors**
   - Add an OpenAlex API key
   - Reduce `UPDATE_MAX_RECORDS`
   - Add delays between requests

3. **Database connection errors**
   - Check `POSTGRES_URL` format
   - Verify PostgreSQL is running
   - Check network connectivity

4. **Memory issues during updates**
   - Reduce `UPDATE_BATCH_SIZE`
   - Reduce `UPDATE_MAX_RECORDS`
   - Run updates more frequently with smaller batches

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set log level
export LOG_LEVEL=DEBUG
get-openalex update

# Or use Python logging
PYTHONLOGGING=DEBUG get-openalex update
```

### Check System Status

```bash
# View recent jobs
get-openalex jobs

# Check specific job (from API)
curl http://localhost:8000/jobs/1

# View job logs (from API)
curl http://localhost:8000/jobs/1/logs
```

## Best Practices

1. **Start Small**: Test with `--max-records 100` first
2. **Use Dry Run**: Test with `--dry-run` to validate setup
3. **Monitor Jobs**: Regularly check job status with `jobs` command
4. **Set Up Logging**: Direct output to log files for automation
5. **Use API Keys**: Get an OpenAlex API key for better rate limits
6. **Regular Updates**: Run daily updates to minimize data lag
7. **Error Handling**: Check failed jobs and retry if needed
8. **Resource Planning**: Monitor memory and CPU usage during updates

## Examples Scripts

### Update Script with Error Handling

```bash
#!/bin/bash
# safe-update.sh

set -e

# Load environment
source /path/to/.env

# Run update with error handling
if get-openalex update --max-records 50000; then
    echo "Update successful"
    # Send success notification
else
    echo "Update failed"
    # Send failure alert
    exit 1
fi
```

### Progressive Update Script

```python
#!/usr/bin/env python
# progressive_update.py

import subprocess
from datetime import datetime, timedelta

# Start from 7 days ago
current_date = datetime.now() - timedelta(days=7)
end_date = datetime.now()

# Update day by day
while current_date < end_date:
    date_str = current_date.strftime("%Y-%m-%d")
    print(f"Updating from {date_str}")
    
    result = subprocess.run([
        "get-openalex", "update",
        "--from-date", date_str,
        "--max-records", "10000"
    ])
    
    if result.returncode != 0:
        print(f"Failed to update from {date_str}")
        break
    
    current_date += timedelta(days=1)
```

## API Integration

The CLI can work alongside the REST API:

```python
import requests
import subprocess

# Start the API server
api_process = subprocess.Popen(["get-openalex", "serve"])

# Use the API
response = requests.post("http://localhost:8000/update", json={
    "job_type": "WORKS_UPDATE",
    "from_date": "2025-01-01",
    "max_records": 1000
})

job_id = response.json()["id"]
print(f"Started job {job_id}")

# Check status
status = requests.get(f"http://localhost:8000/jobs/{job_id}")
print(status.json())

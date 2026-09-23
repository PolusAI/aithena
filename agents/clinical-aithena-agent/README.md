# Clinical Aithena

Clinical Aithena provides tools for managing and querying clinical trial data from ClinicalTrials.gov.

## Components

- **CLI**: Command-line interface for database initialization and data management
- **API**: FastAPI REST API for querying clinical trials data
- **Database**: PostgreSQL with pgvector extension for storing trial data and embeddings

## API

A FastAPI-based REST API for querying clinical trials data.

### Quick Start with Docker Compose

```bash
# Start API and database
docker compose up -d

# Access the API
open http://localhost:8000/docs  # Swagger UI
open http://localhost:8000/health  # Health check
```

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check and database connectivity
- `GET /stats` - ClinicalTrials.gov statistics
- `GET /search` - Search clinical trials (with pagination and keyword filtering)

📚 **For complete Docker deployment guide, see [docs/API_DOCKER.md](docs/API_DOCKER.md)**

## CLI - Available Commands

### `initdb` - Initialize Database

Initialize the PostgreSQL database with tables and indexes for storing clinical trial data.

```bash
ct-aithena initdb [--url URL] [--drop]
```

**Options:**
- `--url URL`: Database connection URL (default: `postgresql://postgres:postgres@localhost:5432/clinical_aithena`)
- `--drop`: Drop existing tables before creating (⚠️ DESTRUCTIVE - will prompt for confirmation)

**Examples:**

```bash
# Initialize with default settings
ct-aithena initdb

# Initialize with custom database URL
ct-aithena initdb --url postgresql://user:pass@localhost:5432/mydb

# Recreate all tables (will prompt for confirmation)
ct-aithena initdb --drop
```

**What it does:**
1. Enables pgvector extension
2. Creates `ctgovstudy` table with:
   - JSONB columns for document storage
   - 8 generated columns for frequently queried fields
   - 14 indexes (3 GIN, 8 B-tree, 2 composite, 1 primary key)
3. Verifies table, indexes, and generated columns

## Adding New Commands

To add a new command to the CLI:

1. **Create command file** in `commands/` directory:
   ```python
   # commands/mycommand.py
   import argparse
   
   def mycommand_command(args: argparse.Namespace) -> int:
       """Execute the mycommand command."""
       # Your command logic here
       print(f"Running mycommand with arg: {args.some_arg}")
       return 0
   ```

2. **Register command** in `main.py`:
   ```python
   from polus.aithena.clinical_aithena.cli.commands.mycommand import mycommand_command
   
   # In main() function, add:
   mycommand_parser = subparsers.add_parser(
       "mycommand", help="Description of mycommand"
   )
   mycommand_parser.add_argument(
       "--some-arg", type=str, help="Some argument"
   )
   mycommand_parser.set_defaults(func=mycommand_command)
   ```

3. **Test the command**:
   ```bash
   ct-aithena mycommand --help
   ct-aithena mycommand --some-arg value
   ```

## CLI Architecture

```
cli/
├── __init__.py
├── main.py                 # CLI entry point with argparse setup
├── commands/
│   ├── __init__.py
│   └── initdb.py          # initdb command implementation
└── README.md              # This file
```

## Entry Point

The CLI is registered as `ct-aithena` in `pyproject.toml`:

```toml
[project.scripts]
ct-aithena = "polus.aithena.clinical_aithena.cli.main:main"
```

After installing the package with `pip install -e .`, the `ct-aithena` command becomes available globally.

## Kubernetes Deployment

The database is deployed to Kubernetes using PostgreSQL with pgvector extension in the `clinical-aithena` namespace.

### Quick Deploy

```bash
cd deployment/

# 1. Create secret from template and edit with your credentials
cp secret.yaml.template secret.yaml
nano secret.yaml

# 2. Deploy (choose one)
./deploy.sh  # Automated (recommended)
# OR
kubectl apply -f .  # Manual

# 3. Monitor deployment
kubectl -n clinical-aithena get pods -w
```

### Connection Details

**Internal (from pods):**
```
# Admin/write access
postgresql://ctgov:pass@clinical-aithena-db-0.clinical-aithena-db.clinical-aithena.svc.cluster.local:5432/clinical_aithena

# Read-only access
postgresql://ctgov_readonly:pass@clinical-aithena-db-0.clinical-aithena-db.clinical-aithena.svc.cluster.local:5432/clinical_aithena
```

**External (port-forward):**
```bash
kubectl -n clinical-aithena port-forward clinical-aithena-db-0 5432:5432

# Admin/write: postgresql://ctgov:pass@localhost:5432/clinical_aithena
# Read-only: postgresql://ctgov_readonly:pass@localhost:5432/clinical_aithena
```

### Key Features

- **pgvector extension** for embeddings
- **500Gi persistent storage** in `.data/` directory
- **8 cores / 16Gi memory** (configurable)
- **Monitoring views** for table sizes and slow queries
- **Utility functions** for bulk operations

📚 **For complete documentation, troubleshooting, backup/recovery, and customization options, see [deployment/README.md](deployment/README.md)**

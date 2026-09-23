# Clinical Aithena Kubernetes Deployment

This directory contains all Kubernetes deployment configurations for the Clinical Aithena system.

## Directory Structure

```
deployment/
├── namespace.yaml          # Shared namespace for all components
├── postgres/              # PostgreSQL database deployment
│   ├── deploy.sh          # Deploy PostgreSQL
│   ├── cleanup.sh         # Clean up PostgreSQL
│   ├── statefulset.yaml   # PostgreSQL StatefulSet
│   ├── headless-service.yaml
│   ├── postgres-config.yaml
│   ├── postgres-init-scripts.yaml
│   ├── pv.yaml
│   ├── secret.yaml.template
│   └── README.md          # Detailed PostgreSQL documentation
├── jobs/                  # Database initialization and sync jobs
│   ├── deploy-jobs.sh     # Deploy jobs
│   ├── build.sh           # Build Docker images for jobs
│   ├── push.sh            # Push Docker images
│   ├── initdb-job.yaml    # One-time database initialization
│   ├── updatedb-cronjob.yaml  # Daily database sync
│   ├── updatedb-job.yaml  # Manual database sync
│   ├── Dockerfile.initdb
│   ├── Dockerfile.updatedb
│   └── README.md          # Detailed jobs documentation
└── api/                   # FastAPI application deployment
    ├── deploy-api.sh      # Deploy API
    ├── cleanup-api.sh     # Clean up API
    ├── api-deployment.yaml
    ├── api-service.yaml
    ├── api-config.yaml
    ├── api-secret.yaml.template
    ├── api-ingress.yaml
    └── README.md          # Detailed API documentation
```

## Deployment Order

The components must be deployed in this order:

### 1. PostgreSQL Database

Deploy the PostgreSQL database with pgvector extension:

```bash
cd postgres
./deploy.sh
```

This creates:
- Namespace: `clinical-aithena`
- StatefulSet with PostgreSQL + pgvector
- PersistentVolume for data storage
- Headless service for StatefulSet
- ConfigMaps and Secrets

**Wait for the database to be ready** before proceeding:

```bash
microk8s kubectl -n clinical-aithena get pods -w
```

Wait until `clinical-aithena-db-0` shows `Running` and `1/1 READY`.

### 2. Database Jobs

Initialize and populate the database:

```bash
cd ../jobs

# Build Docker images (if not already built)
./build.sh v1.0.0

# Deploy jobs
./deploy-jobs.sh
```

This creates:
- `initdb` job: One-time database schema initialization
- `updatedb` CronJob: Daily sync from ClinicalTrials.gov (runs at 2 AM UTC)
- Optional: Manual `updatedb` job for immediate sync

**Monitor the initdb job**:

```bash
microk8s kubectl -n clinical-aithena logs -l component=initdb -f
```

Wait for initdb to complete before deploying the API.

### 3. FastAPI Application

Deploy the REST API:

```bash
cd ../api
./deploy-api.sh
```

This creates:
- Deployment with 2 replicas
- Service (ClusterIP)
- ConfigMap for API settings
- Secret for database credentials (read-only user)
- Ingress for external access

**Access the API**:

- Internal: `http://clinical-aithena-api.clinical-aithena.svc.cluster.local:8000`
- External: `https://polus1.ncats.nih.gov/apis/ctaithena`
- Docs: `https://polus1.ncats.nih.gov/apis/ctaithena/docs`

## Quick Start

For a complete deployment from scratch:

```bash
# 1. Deploy PostgreSQL
cd deployment/postgres
./deploy.sh

# Wait for database to be ready
microk8s kubectl -n clinical-aithena get pods -w

# 2. Build and deploy jobs
cd ../jobs
./build.sh v1.0.0
./deploy-jobs.sh

# Wait for initdb to complete
microk8s kubectl -n clinical-aithena logs -l component=initdb -f

# 3. Deploy API
cd ../api
./deploy-api.sh
```

## Monitoring

### Check all resources:

```bash
microk8s kubectl -n clinical-aithena get all
```

### Check database status:

```bash
microk8s kubectl -n clinical-aithena exec clinical-aithena-db-0 -- psql -U ctgov -d clinical_aithena -c "
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT nct_id) as unique_studies,
    COUNT(*) FILTER (WHERE is_latest = true) as latest_versions
FROM ctgovstudy;
"
```

### Check API logs:

```bash
microk8s kubectl -n clinical-aithena logs -l app=clinical-aithena-api -f
```

### Check job status:

```bash
microk8s kubectl -n clinical-aithena get jobs
microk8s kubectl -n clinical-aithena get cronjobs
```

## Cleanup

To remove components (in reverse order):

```bash
# Remove API
cd api
./cleanup-api.sh

# Remove jobs
microk8s kubectl -n clinical-aithena delete job --all
microk8s kubectl -n clinical-aithena delete cronjob --all

# Remove PostgreSQL (⚠️ deletes all data!)
cd ../postgres
./cleanup.sh
```

## Configuration

### PostgreSQL

- **Admin user**: `ctgov` (full access)
- **Read-only user**: `ctgov_readonly` (for API)
- **Database**: `clinical_aithena`
- **Port**: 5432
- **Storage**: 100Gi PersistentVolume

See `postgres/README.md` for detailed configuration options.

### Jobs

- **initdb**: Runs once to create schema
- **updatedb**: Runs daily at 2 AM UTC via CronJob
- **Docker images**: `polusai/ctaithena-initdb` and `polusai/ctaithena-updatedb`

See `jobs/README.md` for manual job triggering and troubleshooting.

### API

- **Replicas**: 2 (for high availability)
- **Port**: 8000
- **Base path**: `/apis/ctaithena`
- **Database**: Read-only connection to PostgreSQL
- **CORS**: Configurable via `api-config.yaml`

See `api/README.md` for API configuration and usage.

## Troubleshooting

### Database not starting

```bash
microk8s kubectl -n clinical-aithena describe pod clinical-aithena-db-0
microk8s kubectl -n clinical-aithena logs clinical-aithena-db-0
```

### Jobs failing

```bash
microk8s kubectl -n clinical-aithena get jobs
microk8s kubectl -n clinical-aithena logs -l component=initdb
microk8s kubectl -n clinical-aithena logs -l component=updatedb
```

### API not accessible

```bash
microk8s kubectl -n clinical-aithena get pods -l app=clinical-aithena-api
microk8s kubectl -n clinical-aithena logs -l app=clinical-aithena-api
microk8s kubectl -n clinical-aithena describe ingress clinical-aithena-api
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│                                                              │
│  ┌──────────────┐                                           │
│  │   Ingress    │ (polus1.ncats.nih.gov/apis/ctaithena)    │
│  └──────┬───────┘                                           │
│         │                                                    │
│  ┌──────▼───────┐                                           │
│  │  API Service │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│  ┌──────▼────────────────┐                                 │
│  │  API Pods (x2)        │                                 │
│  │  - FastAPI            │                                 │
│  │  - Read-only DB conn  │                                 │
│  └──────┬────────────────┘                                 │
│         │                                                    │
│  ┌──────▼──────────────────────────────────────┐          │
│  │  PostgreSQL StatefulSet                      │          │
│  │  - pgvector extension                        │          │
│  │  - 100Gi PersistentVolume                   │          │
│  │  - Admin user: ctgov                        │          │
│  │  - Read-only user: ctgov_readonly           │          │
│  └──────▲──────────────────────────────────────┘          │
│         │                                                    │
│  ┌──────┴────────┐     ┌────────────────┐                 │
│  │  initdb Job   │     │ updatedb       │                 │
│  │  (one-time)   │     │ CronJob        │                 │
│  │               │     │ (daily 2 AM)   │                 │
│  └───────────────┘     └────────────────┘                 │
│         │                      │                            │
│         └──────────────────────┘                            │
│                │                                             │
│         Fetch from ClinicalTrials.gov API                   │
└─────────────────────────────────────────────────────────────┘
```

## Security Considerations

1. **Database Access**:
   - Admin credentials stored in Kubernetes Secret
   - API uses read-only database user
   - Secrets should be created from template and never committed

2. **Network**:
   - Database not exposed externally
   - API accessible via Ingress with TLS
   - Rate limiting configured on Ingress

3. **API**:
   - CORS configured for allowed origins
   - SQL injection protection via SQLAlchemy ORM
   - Input validation via Pydantic models

## Performance Tuning

- **Database**: Adjust `shared_buffers`, `work_mem` in `postgres-config.yaml`
- **API**: Scale replicas in `api-deployment.yaml`
- **Jobs**: Adjust batch sizes and concurrency in job environment variables

## Support

For detailed documentation on each component:
- PostgreSQL: See `postgres/README.md`
- Jobs: See `jobs/README.md`
- API: See `api/README.md`

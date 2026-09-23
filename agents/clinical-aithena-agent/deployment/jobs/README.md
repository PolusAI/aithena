# Clinical Aithena Database Jobs

Kubernetes manifests for running database initialization and daily sync jobs.

## Overview

### Manifests
- **`initdb-job.yaml`** - One-time initialization job to set up database schema
- **`updatedb-cronjob.yaml`** - Daily CronJob running full pipeline (updatedb → transform → embed)
- **`updatedb-job.yaml`** - One-time pipeline job (optional, for immediate run)

### Pipeline Steps
The updatedb jobs now run the complete pipeline:
1. **updatedb**: Download new/updated trials from ClinicalTrials.gov
2. **transform**: Convert CTGovStudy → TrialGPTStudy format
3. **embed**: Generate MedCPT embeddings for vector search

### Scripts
- **`deploy-jobs.sh`** - Automated deployment with optional immediate run
- **`build.sh`** - Build both Docker images with versioning
- **`push.sh`** - Push both Docker images to registry

### Docker Images
- **`Dockerfile.initdb`** - Dockerfile for initdb job → `polusai/ctaithena-initdb`
- **`Dockerfile.updatedb`** - Dockerfile for updatedb job → `polusai/ctaithena-updatedb`

## Prerequisites

1. **Database deployed:** The pgvector database must be running in the `clinical-aithena` namespace
2. **Container image:** Build and push your `clinical-aithena` Docker image to a registry
3. **Update manifests:** Replace `your-registry/clinical-aithena:latest` with your actual image

## Quick Start

### 1. Build and Push Container Images

```bash
# From project root
cd /polus1/schaubnj/clinical-aithena/agents/clinical-aithena-agent/

# Build both images (with version tag)
./deployment/jobs/build.sh v1.0.0

# Or build with latest tag only
./deployment/jobs/build.sh

# Push to Docker Hub (requires login)
docker login
./deployment/jobs/push.sh v1.0.0

# Or push to a different registry
./deployment/jobs/build.sh v1.0.0 myregistry.com
./deployment/jobs/push.sh v1.0.0 myregistry.com
```

**Images created:**
- `polusai/ctaithena-initdb:latest` - One-time database initialization
- `polusai/ctaithena-updatedb:latest` - Daily database updates

**Base:** Canonical's official `ubuntu/python:3.12-22.04_stable` image

### 2. Verify Images

```bash
# Check local images
docker images | grep ctaithena

# Test initdb image
docker run --rm polusai/ctaithena-initdb:latest ct-aithena --help

# Test updatedb image
docker run --rm polusai/ctaithena-updatedb:latest ct-aithena --help
```

### 3. Deploy to Kubernetes

The job manifests are already configured with the correct image names. Just apply them:

#### Run One-Time Initialization

```bash
# Deploy and run the initialization job
kubectl apply -f deployment/jobs/initdb-job.yaml

# Monitor progress (follow logs)
kubectl -n clinical-aithena logs -l app=clinical-aithena-initdb -f

# Wait for completion (with 10 minute timeout)
kubectl -n clinical-aithena wait --for=condition=complete \
  job/clinical-aithena-initdb --timeout=600s

# Verify database has data
kubectl -n clinical-aithena exec -it clinical-aithena-db-0 -- \
  psql -U ctgov -d clinical_aithena -c "SELECT COUNT(*) FROM ctgovstudy;"

# Clean up completed job (optional)
kubectl -n clinical-aithena delete job clinical-aithena-initdb
```

### 4. Deploy Daily Sync CronJob

#### Option 1: Using Deployment Script (Recommended)

```bash
# Deploy and optionally run immediately
./deployment/jobs/deploy-jobs.sh

# The script will:
# 1. Deploy the CronJob
# 2. Ask if you want to run updatedb immediately
# 3. Provide monitoring commands
```

#### Option 2: Manual Deployment

```bash
# Deploy the CronJob
kubectl apply -f deployment/jobs/updatedb-cronjob.yaml

# Verify it's scheduled
kubectl -n clinical-aithena get cronjob clinical-aithena-updatedb

# Expected output:
# NAME                        SCHEDULE    SUSPEND   ACTIVE   LAST SCHEDULE   AGE
# clinical-aithena-updatedb   0 2 * * *   False     0        <none>          5s
```

#### Option 3: Run Immediately After Deployment

If you want to run an initial update immediately without waiting for the cron schedule:

**Method A: Manually trigger from CronJob (after deploying CronJob)**

```bash
# Create a one-time job from the CronJob
kubectl create job --from=cronjob/clinical-aithena-updatedb \
  clinical-aithena-updatedb-manual-$(date +%Y%m%d-%H%M%S) \
  -n clinical-aithena

# Monitor the job
kubectl -n clinical-aithena get jobs -l component=updatedb
kubectl -n clinical-aithena logs -l component=updatedb -f
```

**Method B: Deploy separate one-time Job**

```bash
# Deploy the one-time job (runs once immediately)
kubectl apply -f deployment/jobs/updatedb-job.yaml

# Monitor progress
kubectl -n clinical-aithena logs -l component=updatedb -f

# Clean up after completion
kubectl -n clinical-aithena delete job clinical-aithena-updatedb-initial
```

**Note:** The CronJob will continue to run on its schedule (2 AM UTC daily) regardless of which method you use for the initial run.

## Monitoring

### View CronJob Status

```bash
# Check CronJob configuration
kubectl -n clinical-aithena get cronjob clinical-aithena-updatedb

# View recent job runs
kubectl -n clinical-aithena get jobs -l app=clinical-aithena-updatedb

# See last 5 job runs with status
kubectl -n clinical-aithena get jobs -l app=clinical-aithena-updatedb \
  --sort-by=.metadata.creationTimestamp | tail -5
```

### View Logs

```bash
# Logs from most recent run
kubectl -n clinical-aithena logs -l app=clinical-aithena-updatedb --tail=100 -f

# Logs from specific job (replace with actual job name)
kubectl -n clinical-aithena logs job/clinical-aithena-updatedb-28435560

# Logs from all recent runs
kubectl -n clinical-aithena logs -l component=updatedb --tail=50
```

### Check Job History

```bash
# See which jobs succeeded/failed
kubectl -n clinical-aithena get jobs -l app=clinical-aithena-updatedb \
  -o custom-columns=NAME:.metadata.name,STATUS:.status.succeeded,FAILED:.status.failed,START:.status.startTime
```

## Manual Operations

### Manually Trigger Update (for testing)

```bash
# Create a manual job from the CronJob template
kubectl -n clinical-aithena create job updatedb-manual-$(date +%s) \
  --from=cronjob/clinical-aithena-updatedb

# Monitor the manual job
kubectl -n clinical-aithena logs -l app=clinical-aithena-updatedb -f --tail=100
```

### Suspend/Resume CronJob

```bash
# Pause the CronJob (stops scheduling new runs)
kubectl -n clinical-aithena patch cronjob clinical-aithena-updatedb \
  -p '{"spec":{"suspend":true}}'

# Resume the CronJob
kubectl -n clinical-aithena patch cronjob clinical-aithena-updatedb \
  -p '{"spec":{"suspend":false}}'
```

### Change Schedule

```bash
# Update to run at 6 AM UTC instead of 2 AM
kubectl -n clinical-aithena patch cronjob clinical-aithena-updatedb \
  -p '{"spec":{"schedule":"0 6 * * *"}}'

# Common schedules:
#   "0 2 * * *"    = 2:00 AM UTC daily
#   "0 */6 * * *"  = Every 6 hours
#   "0 0 * * 0"    = Weekly on Sunday at midnight
#   "0 0 1 * *"    = Monthly on the 1st at midnight
```

## Troubleshooting

### Job Failed

```bash
# Check job status
kubectl -n clinical-aithena describe job <job-name>

# View logs from failed pod
kubectl -n clinical-aithena logs <pod-name>

# Delete failed job to allow CronJob to create a new one
kubectl -n clinical-aithena delete job <job-name>
```

### Job Stuck in Pending

```bash
# Check pod status
kubectl -n clinical-aithena get pods -l app=clinical-aithena-updatedb

# Describe pod to see why it's not starting
kubectl -n clinical-aithena describe pod <pod-name>

# Common issues:
# - Image pull error: Check image name and registry access
# - Resource constraints: Check cluster has enough CPU/memory
# - Secret missing: Verify clinical-aithena-db-secret exists
```

### Database Connection Issues

```bash
# Test database connectivity from a pod
kubectl -n clinical-aithena run -it --rm debug \
  --image=postgres:17 \
  --restart=Never \
  -- psql -h clinical-aithena-db-0.clinical-aithena-db.clinical-aithena.svc.cluster.local \
        -U ctgov -d clinical_aithena -c "SELECT 1;"

# Check database service
kubectl -n clinical-aithena get service clinical-aithena-db

# Check database pod
kubectl -n clinical-aithena get pods clinical-aithena-db-0
```

### Concurrent Job Prevention

The CronJob is configured with `concurrencyPolicy: Forbid` to prevent overlapping runs.

```bash
# If a job is stuck, you may need to manually delete it
kubectl -n clinical-aithena get jobs -l app=clinical-aithena-updatedb
kubectl -n clinical-aithena delete job <stuck-job-name>
```

## Resource Tuning

### Adjust Resources Based on Data Size

Edit the job manifests to adjust resource limits:

```yaml
resources:
  requests:
    memory: "2Gi"   # Minimum memory
    cpu: "2"        # Minimum CPU
  limits:
    memory: "8Gi"   # Maximum memory
    cpu: "7"        # Maximum CPU (matches ProcessPoolExecutor workers)
```

**Guidelines:**
- **CPU:** Set based on your multiprocessing configuration (cpu_count - 1)
- **Memory:** Monitor actual usage and adjust; 8Gi should handle ~500k trials
- **Small datasets (<100k trials):** Use lower limits (4Gi memory, 2-4 CPUs)
- **Large datasets (>500k trials):** May need higher limits (16Gi memory, 8+ CPUs)

### Monitor Resource Usage

```bash
# Watch resource usage during job execution
kubectl -n clinical-aithena top pod -l app=clinical-aithena-updatedb

# View historical resource usage (if metrics-server is installed)
kubectl -n clinical-aithena describe pod <pod-name> | grep -A 5 "Resource"
```

## Clean Up

### Remove All Jobs

```bash
# Delete the CronJob (stops future runs)
kubectl -n clinical-aithena delete cronjob clinical-aithena-updatedb

# Delete job history
kubectl -n clinical-aithena delete jobs -l app=clinical-aithena-updatedb

# Delete initdb job if still present
kubectl -n clinical-aithena delete job clinical-aithena-initdb
```

## Advanced Configuration

### Add Slack/Email Notifications

You can add a notification sidecar container or use Kubernetes events with a monitoring tool like:
- Prometheus Alertmanager
- Kubewatch
- Botkube

### Integrate with Argo CD (GitOps)

```bash
# Add jobs to your Argo CD application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: clinical-aithena-jobs
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/clinical-aithena
    targetRevision: HEAD
    path: deployment/jobs
  destination:
    server: https://kubernetes.default.svc
    namespace: clinical-aithena
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

## Related Documentation

- Main deployment: [../README.md](../README.md)
- Database setup: [../README.md](../README.md)
- Work items: **CLAIT-13** (CronJob), **CLAIT-15** (initdb Job)

## Scheduling Considerations

**Best practices for schedule selection:**

1. **Off-peak hours:** Run during low cluster usage (typically 1-4 AM)
2. **ClinicalTrials.gov load:** Consider API rate limits and their peak times
3. **Database maintenance:** Avoid scheduled backup/maintenance windows
4. **Time zones:** CronJob uses UTC, convert your local time accordingly

**Example schedules:**

```bash
# 2 AM UTC = 9 PM EST / 6 PM PST
"0 2 * * *"

# 6 AM UTC = 1 AM EST / 10 PM PST
"0 6 * * *"

# Every 12 hours
"0 */12 * * *"

# Weekly on Sunday at midnight UTC
"0 0 * * 0"
```

## Performance Notes

### updatedb (Step 1)
- **Async + Multiprocessing:** Uses asyncio for I/O and ProcessPoolExecutor for CPU-bound tasks
- **Batch processing:** Studies are processed in batches of 1000
- **Backpressure:** Queue size of 2 prevents overwhelming the database
- **Progress tracking:** tqdm configured for Docker/log-friendly output (updates every 10 seconds)
- **Expected duration:** 
  - Initial sync: ~2-3 hours for ~500k trials
  - Daily incremental: ~5-15 minutes

### transform (Step 2)
- **Incremental mode:** Only processes new/updated trials (not in TrialGPTStudy table)
- **Batch processing:** Commits in batches of 100
- **Expected duration:**
  - Initial transform: ~30-60 minutes for 500k trials
  - Daily incremental: ~1-5 minutes for ~100-1000 new trials

### embed (Step 3)
- **Resume mode:** Skips trials that already have embeddings
- **Batch processing:** Generates embeddings in batches of 32
- **MedCPT models:** Uses LiteLLM to access ncbi/MedCPT-Article-Encoder
- **Expected duration:**
  - Initial embed: ~5-10 hours for 500k trials (depends on LiteLLM backend)
  - Daily incremental: ~5-30 minutes for ~100-1000 new trials

### BM25 Index
- **Built dynamically:** No preprocessing needed, index builds in-memory on first search (~1-2 seconds)
- **Auto-refresh:** Can be configured to rebuild when new trials are added
- **No cron job needed:** Handled automatically by the retrieval system

### Total Pipeline Duration
- **Initial run (first time):** ~8-15 hours
- **Daily incremental:** ~10-50 minutes


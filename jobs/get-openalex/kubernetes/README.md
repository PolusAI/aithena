# OpenAlex Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the OpenAlex data synchronization system.

## 📁 Files Overview

- **01-configmap.yaml** - Configuration settings for the application
- **02-secret.yaml** - Sensitive credentials (database passwords, API keys)
- **03-pvc.yaml** - Persistent storage for job database and data
- **04-deployment.yaml** - API server deployment
- **05-service.yaml** - Service and Ingress for API access
- **06-cronjob.yaml** - Scheduled jobs for daily updates

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes cluster** (1.24+ recommended)
2. **kubectl** configured to access your cluster
3. **Docker image** built and pushed to a registry
4. **PostgreSQL database** (optional, for storing OpenAlex data)

### Step 1: Build and Push Docker Image

```bash
# Build the Docker image
docker build -t your-registry/openalex/get-openalex:latest .

# Push to your registry
docker push your-registry/openalex/get-openalex:latest
```

### Step 2: Configure Settings

1. Edit `01-configmap.yaml`:
   - Set `PYALEX_EMAIL` to your email (required by OpenAlex API)
   - Adjust `UPDATE_MAX_RECORDS` based on your needs
   - Set `USE_POSTGRES` to "true" if using PostgreSQL

2. Edit `02-secret.yaml`:
   - Add your `POSTGRES_URL` if using PostgreSQL
   - Add `OPENALEX_API_KEY` if you have one (for higher rate limits)

3. Update image references in:
   - `04-deployment.yaml`
   - `06-cronjob.yaml`

### Step 3: Deploy to Kubernetes

```bash
# Create namespace (optional)
kubectl create namespace openalex

# Apply all manifests in order
kubectl apply -f 01-configmap.yaml
kubectl apply -f 02-secret.yaml
kubectl apply -f 03-pvc.yaml
kubectl apply -f 04-deployment.yaml
kubectl apply -f 05-service.yaml
kubectl apply -f 06-cronjob.yaml

# Or apply all at once
kubectl apply -f .
```

### Step 4: Verify Deployment

```bash
# Check if pods are running
kubectl get pods -l app=openalex-api

# Check service
kubectl get svc openalex-api-service

# Check CronJob
kubectl get cronjob openalex-daily-update

# View logs
kubectl logs -l app=openalex-api

# Test the API (port-forward for local access)
kubectl port-forward svc/openalex-api-service 8000:8000
curl http://localhost:8000/health
```

## 📅 Scheduled Jobs

### Daily Update Job
- **Schedule**: Daily at 2 AM UTC
- **Purpose**: Fetch incremental updates from OpenAlex API
- **Configuration**: Adjust schedule in `06-cronjob.yaml`

To run manually:
```bash
kubectl create job --from=cronjob/openalex-daily-update manual-update-$(date +%s)
```

### Monthly Snapshot Job (Optional)
- **Schedule**: Monthly on the 1st at 3 AM UTC
- **Purpose**: Full refresh from S3 snapshots
- **Status**: Suspended by default

To enable:
```bash
kubectl patch cronjob openalex-monthly-snapshot -p '{"spec":{"suspend":false}}'
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PYALEX_EMAIL` | Your email for OpenAlex API (required) | - |
| `OPENALEX_API_KEY` | OpenAlex API key for higher rate limits | - |
| `UPDATE_BATCH_SIZE` | Records per batch | 100 |
| `UPDATE_MAX_RECORDS` | Max records per update job | 10000 |
| `USE_POSTGRES` | Enable PostgreSQL storage | false |
| `POSTGRES_URL` | PostgreSQL connection string | - |
| `JOB_DATABASE_URL` | Job tracking database | sqlite:///data/openalex_jobs.db |

### Storage Requirements

- **Job Database**: 10Gi (SQLite or PostgreSQL)
- **OpenAlex Data**: 50Gi+ (if using PostgreSQL)
- **Temporary Snapshot Storage**: 100Gi (for monthly updates)

### Resource Requirements

| Component | Memory | CPU |
|-----------|--------|-----|
| API Server | 1-2Gi | 0.5-1 cores |
| Daily Update | 2-4Gi | 1-2 cores |
| Monthly Snapshot | 8-16Gi | 2-4 cores |

## 🌐 External Access

### Option 1: Port Forwarding (Development)
```bash
kubectl port-forward svc/openalex-api-service 8000:8000
```

### Option 2: NodePort
Edit `05-service.yaml`:
```yaml
spec:
  type: NodePort
  ports:
  - port: 8000
    nodePort: 30080  # Choose a port 30000-32767
```

### Option 3: LoadBalancer
Edit `05-service.yaml`:
```yaml
spec:
  type: LoadBalancer
```

### Option 4: Ingress (Production)
1. Install an ingress controller (e.g., nginx-ingress)
2. Edit the Ingress section in `05-service.yaml`
3. Set your domain name
4. Configure TLS if needed

## 🔍 Monitoring & Debugging

### View Job History
```bash
# List all update jobs
kubectl get jobs | grep openalex

# View specific job logs
kubectl logs job/openalex-daily-update-xxxxx
```

### Check Database
```bash
# Access the pod
kubectl exec -it deployment/openalex-api -- bash

# Use CLI to check jobs
get-openalex jobs

# Run manual update
get-openalex update --max-records 100
```

### Common Issues

1. **Pod not starting**
   - Check logs: `kubectl logs -l app=openalex-api`
   - Verify ConfigMap/Secret: `kubectl describe configmap openalex-config`

2. **CronJob not running**
   - Check schedule: `kubectl get cronjob openalex-daily-update -o yaml`
   - Check job history: `kubectl get jobs`

3. **Storage issues**
   - Check PVC status: `kubectl get pvc`
   - Verify storage class: `kubectl get storageclass`

4. **API rate limits**
   - Add OpenAlex API key in secret
   - Reduce UPDATE_MAX_RECORDS
   - Adjust CronJob schedule

## 🧹 Cleanup

To remove all resources:
```bash
kubectl delete -f .
```

## 📚 Additional Resources

- [OpenAlex API Documentation](https://docs.openalex.org/)
- [Kubernetes CronJob Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Persistent Volumes Documentation](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

## 💡 Tips

1. **Start small**: Test with low `UPDATE_MAX_RECORDS` first
2. **Monitor resources**: Use `kubectl top pods` to check usage
3. **Use namespaces**: Deploy to a dedicated namespace for isolation
4. **Enable autoscaling**: Add HPA for the API deployment if needed
5. **Backup job database**: Regular backups of the job tracking database

## 🤝 Support

For issues or questions:
1. Check the logs first
2. Review environment variables
3. Verify database connectivity
4. Check OpenAlex API status

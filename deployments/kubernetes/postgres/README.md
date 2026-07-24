# PostgreSQL Deployment

This directory contains the Kubernetes deployment for the main PostgreSQL database, optimized for OpenAlex data.

## Description
This is the primary data store for AskAithena, enabled with `pgvector` to store and query high-dimensional vector embeddings of scientific literature.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.
- **Secrets**: You need to create the `askaithena-db-secret`.
- **Storage Class**: We define a custom storage class in this directory called `truly-manual`. It is a storage class that does not provision volumes, but rather uses the host path directly.

### 0. Apply the storage class
```bash
microk8s kubectl apply -f manual-storage-class.yaml
```

### 1. Create Secret

Copy the sample secret and fill in your actual values:

```bash
cp secret_sample.yaml secret.yaml
```

### 2. Edit the secret
Edit the secret.yaml file with:
- `username`: The database username (default: admin).
- `password`: The database password.

These need to be base64 encoded.

```bash
echo -n "your-secure-password" | base64
```
Don't forget to include `-n` to echo the password without a newline.

### 3. Apply the secret

Apply the secret:
```bash
microk8s kubectl apply -f secret.yaml
```

### 4. Edit pv.yaml

Edit the pv.yaml file with:
- `hostPath.path`: The path where the database data is stored in the host filesystem.

### 5. Edit statefulset.yaml

Edit the statefulset.yaml file with:
- `env.POSTGRES_DB`: The database name (default: askaithena).

## Deployment

**Note**: This deployment uses a Two-Phase Strategy (Loading vs Production). See the detailed guide below for specific instructions.

### Quick Start (Loading Phase)

```bash
# Storage
microk8s kubectl apply -f pv.yaml

# Configs
microk8s kubectl apply -f configs/loading/postgresql-config-loading.yaml
microk8s kubectl apply -f configs/loading/init-scripts-config-loading.yaml

# Services
microk8s kubectl apply -f headless-service.yaml
microk8s kubectl apply -f service.yaml

# StatefulSet
microk8s kubectl apply -f statefulset.yaml
```

## Verification
Check if the pods are running:
```bash
microk8s kubectl -n box get pods -l app=askaithena-db
```

---

# Detailed Guide: High-Performance PostgreSQL for OpenAlex

This deployment is optimized for loading and querying the OpenAlex dataset on a powerful single-node server.

## Two-Phase Deployment Strategy

We use different configurations for loading vs production to maximize performance:
- **Loading Phase**: Minimal extensions, no monitoring overhead, aggressive bulk-load settings
- **Production Phase**: Full monitoring, query tracking, balanced performance settings

## Files Overview

### Core Files
- **pv.yaml** - Static PersistentVolume (10Ti) at `/polus2/velezramirezc2/.data/askaithena`
- **statefulset.yaml** - PostgreSQL StatefulSet with 110 CPU/500Gi memory limits
- **headless-service.yaml** - Service for StatefulSet DNS resolution

### Configuration Sets

#### Loading Phase (Maximum Performance)
- `configs/loading/postgresql-config-loading.yaml` - No pg_stat_statements, aggressive bulk-load settings
- `configs/loading/init-scripts-config-loading.yaml` - Minimal extensions (vector, pg_trgm)

#### Production Phase (Full Features)
- `configs/production/postgresql-config-production.yaml` - Includes pg_stat_statements
- `configs/production/init-scripts-config-production.yaml` - All extensions and monitoring views
- `configs/production/post-load-monitoring.sql` - Post-deployment monitoring setup

## Phase 1: Loading Deployment

1. **Deploy with loading configurations:**
   ```bash
   # Create the PersistentVolume
   microk8s kubectl apply -f pv.yaml
   
   # Apply LOADING phase ConfigMaps
   microk8s kubectl apply -f configs/loading/postgresql-config-loading.yaml
   microk8s kubectl apply -f configs/loading/init-scripts-config-loading.yaml
   
   # Create the headless service
   microk8s kubectl apply -f headless-service.yaml
   
   # Update StatefulSet to use loading configs
   # Edit statefulset.yaml to reference:
   # - postgres-config-loading
   # - postgres-init-scripts-loading
   
   # Deploy PostgreSQL StatefulSet
   microk8s kubectl apply -f statefulset.yaml
   ```

2. **Monitor deployment:**
   ```bash
   # Watch the StatefulSet
   microk8s kubectl -n box get statefulset askaithena-db -w
   
   # View init container logs
   microk8s kubectl -n box logs askaithena-db-0 -c postgres-init
   
   # View PostgreSQL logs
   microk8s kubectl -n box logs askaithena-db-0 -c postgres -f
   ```

3. **Load OpenAlex data:**
   ```bash
   # Use your optimized loading scripts
   python scripts/upload_1.py
   
   # Or use the utility functions:
   microk8s kubectl -n box exec -it askaithena-db-0 -- psql -U YOUR_USERNAME -d askaithena
   
   # Disable indexes before bulk load:
   SELECT * FROM openalex.disable_indexes('openalex', 'works');
   
   # After loading, optimize tables:
   SELECT openalex.optimize_table('openalex.works');
   ```

## Phase 2: Switch to Production

1. **Apply production configurations:**
   ```bash
   # Delete loading configs
   microk8s kubectl delete configmap postgres-config-loading -n box
   microk8s kubectl delete configmap postgres-init-scripts-loading -n box
   
   # Apply production configs
   microk8s kubectl apply -f configs/production/postgresql-config-production.yaml
   microk8s kubectl apply -f configs/production/init-scripts-config-production.yaml
   ```

2. **Update StatefulSet and restart:**
   ```bash
   # Edit statefulset.yaml to reference:
   # - postgres-config-production (instead of postgres-config-loading)
   # - postgres-init-scripts-production (instead of postgres-init-scripts-loading)
   
   # Apply the change
   microk8s kubectl apply -f statefulset.yaml
   
   # Restart PostgreSQL (clean restart in Kubernetes)
   microk8s kubectl -n box delete pod askaithena-db-0
   
   # Wait for it to come back up
   microk8s kubectl -n box get pod askaithena-db-0 -w
   ```

3. **Apply post-load monitoring:**
   ```bash
   # Connect and run the monitoring setup
   microk8s kubectl -n box exec -it askaithena-db-0 -- psql -U YOUR_USERNAME -d askaithena \
     -f /configs/production/post-load-monitoring.sql
   
   # Or copy and run:
   microk8s kubectl cp configs/production/post-load-monitoring.sql box/askaithena-db-0:/tmp/
   microk8s kubectl -n box exec -it askaithena-db-0 -- psql -U YOUR_USERNAME -d askaithena -f /tmp/post-load-monitoring.sql
   ```


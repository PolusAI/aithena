# High-Performance PostgreSQL for OpenAlex on Kubernetes

This deployment is optimized for loading and querying the OpenAlex dataset on a powerful single-node server (112 cores, 1.4TB RAM).

## Two-Phase Deployment Strategy

We use different configurations for loading vs production to maximize performance:
- **Loading Phase**: Minimal extensions, no monitoring overhead, aggressive bulk-load settings
- **Production Phase**: Full monitoring, query tracking, balanced performance settings

## Files Overview

### Core Files
- **pv.yaml** - Static PersistentVolume (10Ti) at `/polus2/velezramirezc2/.data/askaithena`
- **statefulset.yaml** - PostgreSQL StatefulSet with 110 CPU/500Gi memory limits
- **headless-service.yaml** - Service for StatefulSet DNS resolution
- **monitoring-deployment.yaml** - Optional Prometheus postgres-exporter

### Configuration Sets

#### Loading Phase (Maximum Performance)
- `configs/loading/postgresql-config-loading.yaml` - No pg_stat_statements, aggressive bulk-load settings
- `configs/loading/init-scripts-config-loading.yaml` - Minimal extensions (vector, pg_trgm)

#### Production Phase (Full Features)
- `configs/production/postgresql-config-production.yaml` - Includes pg_stat_statements
- `configs/production/init-scripts-config-production.yaml` - All extensions and monitoring views
- `configs/production/post-load-monitoring.sql` - Post-deployment monitoring setup

## Prerequisites

1. Ensure the secret exists with your database credentials:
   ```bash
   mkk get secret askaithena-db-secret -n box
   ```
   
   If not, create it:
   ```bash
   mkk create secret generic askaithena-db-secret \
     --from-literal=username=YOUR_USERNAME \
     --from-literal=password=YOUR_PASSWORD \
     -n box
   ```

2. Create the data directory:
   ```bash
   mkdir -p /polus2/velezramirezc2/.data/askaithena
   ```

## Phase 1: Loading Deployment

1. **Deploy with loading configurations:**
   ```bash
   # Create the PersistentVolume
   mkk apply -f pv.yaml
   
   # Apply LOADING phase ConfigMaps
   mkk apply -f configs/loading/postgresql-config-loading.yaml
   mkk apply -f configs/loading/init-scripts-config-loading.yaml
   
   # Create the headless service
   mkk apply -f headless-service.yaml
   
   # Update StatefulSet to use loading configs
   # Edit statefulset.yaml to reference:
   # - postgres-config-loading
   # - postgres-init-scripts-loading
   
   # Deploy PostgreSQL StatefulSet
   mkk apply -f statefulset.yaml
   ```

2. **Monitor deployment:**
   ```bash
   # Watch the StatefulSet
   mkk -n box get statefulset askaithena-db -w
   
   # View init container logs
   mkk -n box logs askaithena-db-0 -c postgres-init
   
   # View PostgreSQL logs
   mkk -n box logs askaithena-db-0 -c postgres -f
   ```

3. **Load OpenAlex data:**
   ```bash
   # Use your optimized loading scripts
   python scripts/upload_1.py
   
   # Or use the utility functions:
   mkk -n box exec -it askaithena-db-0 -- psql -U YOUR_USERNAME -d askaithena
   
   # Disable indexes before bulk load:
   SELECT * FROM openalex.disable_indexes('openalex', 'works');
   
   # After loading, optimize tables:
   SELECT openalex.optimize_table('openalex.works');
   ```

## Phase 2: Switch to Production

1. **Apply production configurations:**
   ```bash
   # Delete loading configs
   mkk delete configmap postgres-config-loading -n box
   mkk delete configmap postgres-init-scripts-loading -n box
   
   # Apply production configs
   mkk apply -f configs/production/postgresql-config-production.yaml
   mkk apply -f configs/production/init-scripts-config-production.yaml
   ```

2. **Update StatefulSet and restart:**
   ```bash
   # Edit statefulset.yaml to reference:
   # - postgres-config-production (instead of postgres-config-loading)
   # - postgres-init-scripts-production (instead of postgres-init-scripts-loading)
   
   # Apply the change
   mkk apply -f statefulset.yaml
   
   # Restart PostgreSQL (clean restart in Kubernetes)
   mkk -n box delete pod askaithena-db-0
   
   # Wait for it to come back up
   mkk -n box get pod askaithena-db-0 -w
   ```

3. **Apply post-load monitoring:**
   ```bash
   # Connect and run the monitoring setup
   mkk -n box exec -it askaithena-db-0 -- psql -U YOUR_USERNAME -d askaithena \
     -f /configs/production/post-load-monitoring.sql
   
   # Or copy and run:
   mkk cp configs/production/post-load-monitoring.sql box/askaithena-db-0:/tmp/
   mkk -n box exec -it askaithena-db-0 -- psql -U YOUR_USERNAME -d askaithena -f /tmp/post-load-monitoring.sql
   ```

4. **Deploy monitoring (optional):**
   ```bash
   mkk apply -f monitoring-deployment.yaml
   ```

## Connection Details

- **Internal DNS**: `askaithena-db-0.askaithena-db.box.svc.cluster.local`
- **Port**: 5432
- **Database**: askaithena
- **Schema**: openalex (created automatically)

## Performance Features

### Loading Phase
- No pg_stat_statements overhead
- Minimal WAL logging (`wal_level = minimal`)
- Aggressive checkpoints (60min timeout)
- Reduced autovacuum activity
- JIT disabled

### Production Phase
- Full query monitoring with pg_stat_statements
- Standard WAL logging for safety
- Regular checkpoints (30min)
- Active autovacuum
- JIT enabled for complex queries

## Monitoring Queries (Production Only)

```sql
-- Table sizes
SELECT * FROM monitoring.table_sizes;

-- Unused indexes
SELECT * FROM monitoring.index_usage WHERE usage_status = 'UNUSED';

-- Slow queries
SELECT * FROM monitoring.slow_queries;

-- Current activity
SELECT * FROM monitoring.current_activity;

-- Table bloat
SELECT * FROM monitoring.table_bloat WHERE bloat_pct > 20;

-- Index recommendations
SELECT * FROM monitoring.suggest_indexes();
```

## Utility Functions (Available in Both Phases)

```sql
-- Create multiple indexes efficiently
SELECT openalex.create_indexes_parallel(
    'openalex.works',
    ARRAY[
        'CREATE INDEX idx_works_doi ON openalex.works(doi)',
        'CREATE INDEX idx_works_year ON openalex.works(publication_year)'
    ]
);

-- Optimize table after bulk load
SELECT openalex.optimize_table('openalex.works');

-- Disable indexes before bulk load (loading phase)
SELECT * FROM openalex.disable_indexes('openalex', 'works');
```

## Troubleshooting

1. **Permission Issues**: Check init container logs
   ```bash
   mkk -n box logs askaithena-db-0 -c postgres-init
   ```

2. **Connection Issues**: Verify service and pod
   ```bash
   mkk -n box get svc askaithena-db
   mkk -n box describe pod askaithena-db-0
   ```

3. **Performance Issues**: Check PostgreSQL config
   ```sql
   SHOW shared_buffers;
   SHOW shared_preload_libraries;
   SHOW pg_stat_statements.track;
   ```

4. **Switch Phase Issues**: Ensure ConfigMaps are updated
   ```bash
   mkk -n box get configmap | grep postgres
   ```

## Cleanup (if needed)

To completely remove the deployment:
```bash
# Delete StatefulSet (keeps PVC)
mkk delete -f statefulset.yaml

# Delete PVC (careful - this schedules data deletion!)
mkk -n box delete pvc postgres-storage-askaithena-db-0

# Delete other resources
mkk delete -f headless-service.yaml
mkk delete -f configs/loading/*.yaml
mkk delete -f configs/production/*.yaml
mkk delete -f pv.yaml
mkk delete -f monitoring-deployment.yaml
```

## Best Practices

1. **Always start with loading configuration** for bulk data imports
2. **Switch to production only after** major data loading is complete
3. **Run ANALYZE** after switching to production to update statistics
4. **Monitor unused indexes** and remove them to save space
5. **Use fuzzy search** with pg_trgm for name matching:
   ```sql
   SELECT * FROM openalex.authors 
   WHERE display_name % 'Jon Smith';  -- Finds 'John Smith'
   ```

## Notes

- The StatefulSet uses a static PV to ensure data persists in a known location
- The init container ensures proper permissions (999:999 for PostgreSQL)
- Shared memory is set to 50Gi for large parallel operations
- Configuration changes require pod restart (automatic in Kubernetes)
- The two-phase approach can reduce bulk loading time by 30-50%

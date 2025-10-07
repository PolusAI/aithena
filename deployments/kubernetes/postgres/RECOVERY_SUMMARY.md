# PostgreSQL Recovery Summary

## Problem Identified

Your PostgreSQL container is detecting existing data in `/polus2/velezramirezc2/askaithena_data/jul25` and skipping initialization. This means:
- The `AithenaAdmin` user is never created
- The `askaithena` database may not exist
- Init scripts in `/docker-entrypoint-initdb.d` are not executed

## Root Causes

1. **Persistent Data**: The hostPath directory contains old PostgreSQL data that isn't being properly cleaned
2. **PostgreSQL Docker Behavior**: The official PostgreSQL image ONLY runs initialization when PGDATA is completely empty
3. **Potential Permission Issues**: The directory may have incorrect permissions for the postgres user (UID/GID 999)

## Files Created/Updated

1. **postgres-debug-pod.yaml** - Debug pod to inspect the data directory
2. **postgres-deep-clean.yaml** - Enhanced cleanup pod that removes ALL files including hidden ones
3. **statefulset.yaml** - Updated with init container for permissions (original backed up as statefulset.yaml.backup)
4. **recovery-procedure.sh** - Interactive script guiding through the recovery process

## Quick Recovery Commands

If you want to proceed quickly without the interactive script:

```bash
cd /polus2/velezramirezc2/aithena/deployments/kubernetes/postgres

# 1. Stop current deployment
mkk delete statefulset -n box askaithena-db

# 2. Wait for pods to terminate
mkk get pods -n box -l app=askaithena-db
# Wait until no pods are shown

# 3. Deep clean the data directory
mkk apply -f postgres-deep-clean.yaml
mkk logs -n box postgres-deep-clean -f
# Wait for "Cleanup complete!" message

# 4. Remove cleanup pod
mkk delete pod -n box postgres-deep-clean

# 5. Deploy fixed StatefulSet
mkk apply -f statefulset.yaml

# 6. Monitor deployment
mkk get pods -n box -l app=askaithena-db -w

# 7. Check logs once running
mkk logs -n box -l app=askaithena-db -c postgres --tail=100

# 8. Test connection
psql -U AithenaAdmin -h localhost -d askaithena -p 30432
# Password: polus2has8
```

## What Changed

1. **Added Init Container**: Ensures proper permissions (999:999) on PGDATA before PostgreSQL starts
2. **Enhanced Cleanup**: Removes ALL files including hidden ones (like .s.PGSQL.* lock files)
3. **Better Logging**: Init container logs what it finds and does

## Verification Steps

After deployment, verify initialization was successful by looking for these log messages:

```
The files belonging to this database system will be owned by user "postgres"
initdb: ok
CREATE ROLE
CREATE DATABASE
PostgreSQL init process complete; ready for start up
```

## Troubleshooting

If issues persist:

1. Check init container logs:
   ```bash
   mkk logs -n box -l app=askaithena-db -c fix-permissions
   ```

2. Check if data directory is truly empty:
   ```bash
   mkk apply -f postgres-debug-pod.yaml
   mkk exec -it -n box postgres-debug -- ls -la /data/
   mkk delete pod -n box postgres-debug
   ```

3. Check pod events:
   ```bash
   mkk describe pod -n box -l app=askaithena-db
   ```

## Additional Notes

- The GSSAPI error you saw is normal when Kerberos isn't configured - it falls back to password auth
- The "database already exists" message confirms PostgreSQL is finding old data
- Always ensure the data directory is completely empty for initialization to run

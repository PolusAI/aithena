# StatefulSet Configuration Changes Between Phases

## Loading Phase Configuration

In `statefulset.yaml`, ensure these ConfigMap references:

```yaml
      volumes:
      - name: postgres-config
        configMap:
          name: postgres-config-loading        # <-- LOADING
      - name: init-scripts
        configMap:
          name: postgres-init-scripts-loading  # <-- LOADING
          defaultMode: 0755
```

## Production Phase Configuration

After bulk loading, change to:

```yaml
      volumes:
      - name: postgres-config
        configMap:
          name: postgres-config-production     # <-- PRODUCTION
      - name: init-scripts
        configMap:
          name: postgres-init-scripts-production  # <-- PRODUCTION
          defaultMode: 0755
```

## Quick Switch Commands

```bash
# 1. Edit the StatefulSet
mkk edit statefulset askaithena-db -n box

# 2. Or use sed to make the changes
sed -i 's/postgres-config-loading/postgres-config-production/g' statefulset.yaml
sed -i 's/postgres-init-scripts-loading/postgres-init-scripts-production/g' statefulset.yaml

# 3. Apply the changes
mkk apply -f statefulset.yaml

# 4. Restart the pod
mkk delete pod askaithena-db-0 -n box
```

## Verification

After switching, verify the correct configs are loaded:

```bash
# Check mounted ConfigMaps
mkk -n box describe pod askaithena-db-0 | grep -A5 "Volumes:"

# Inside PostgreSQL
mkk -n box exec -it askaithena-db-0 -- psql -U postgres -c "SHOW shared_preload_libraries;"
# Should show: 'vector' (loading) or 'pg_stat_statements,vector' (production)

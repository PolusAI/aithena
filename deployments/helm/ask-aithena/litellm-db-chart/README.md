# LiteLLM Database Helm Chart

This Helm chart deploys a PostgreSQL database optimized for use with LiteLLM in Kubernetes clusters.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure (for persistent storage)

## Installation

### Add the Repository (if published)

```bash
helm repo add aithena https://github.com/camilovelezr/aithena/charts
helm repo update
```

### Install the Chart

Install the chart with the release name `litellm-db`:

```bash
helm install litellm-db ./litellm-db-chart
```

To install in a specific namespace:

```bash
helm install litellm-db ./litellm-db-chart --namespace box --create-namespace
```

### Install with Custom Values

```bash
helm install litellm-db ./litellm-db-chart -f my-values.yaml
```

## Uninstallation

To uninstall/delete the `litellm-db` deployment:

```bash
helm uninstall litellm-db
```

The command removes all the Kubernetes components associated with the chart and deletes the release.

## Configuration

The following table lists the configurable parameters of the LiteLLM DB chart and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of PostgreSQL replicas | `1` |
| `nameOverride` | String to partially override the fullname | `""` |
| `fullnameOverride` | String to fully override the fullname | `""` |

### Image Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | PostgreSQL image repository | `postgres` |
| `image.tag` | PostgreSQL image tag | `16.4` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `imagePullSecrets` | Image pull secrets | `[]` |

### Authentication Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `auth.database` | Database name | `litellm` |
| `auth.username` | Database username | `llmproxy` |
| `auth.password` | Database password | `litellmpassword` |
| `auth.existingSecret` | Name of existing secret to use | `""` |

### Service Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `5432` |
| `service.targetPort` | Container port | `5432` |
| `service.protocol` | Protocol | `TCP` |
| `service.nodePort` | NodePort (if service.type is NodePort) | `""` |
| `service.annotations` | Service annotations | `{}` |

### Persistence Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistence using PVC | `true` |
| `persistence.size` | PVC Storage Request | `10Gi` |
| `persistence.storageClassName` | Storage Class name | `standard` |
| `persistence.accessMode` | PVC Access Mode | `ReadWriteOnce` |
| `persistence.existingClaim` | Use existing PVC | `""` |
| `persistence.hostPath.enabled` | Use HostPath for storage | `true` |
| `persistence.hostPath.path` | Host path for storage | `/polus2/velezramirezc2/.data/litellm_db_data` |
| `persistence.hostPath.type` | HostPath type | `DirectoryOrCreate` |
| `persistence.reclaimPolicy` | PV reclaim policy | `Retain` |
| `persistence.volumeName` | PV name (optional) | `""` |

### Resource Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.cpu` | CPU limit | `1000m` |
| `resources.limits.memory` | Memory limit | `1Gi` |
| `resources.requests.cpu` | CPU request | `250m` |
| `resources.requests.memory` | Memory request | `256Mi` |

### Health Check Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `probes.enabled` | Enable liveness and readiness probes | `true` |
| `probes.readiness.initialDelaySeconds` | Readiness probe initial delay | `5` |
| `probes.readiness.periodSeconds` | Readiness probe period | `10` |
| `probes.liveness.initialDelaySeconds` | Liveness probe initial delay | `15` |
| `probes.liveness.periodSeconds` | Liveness probe period | `20` |

### Security Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podSecurityContext.fsGroup` | Group ID for the pod | `999` |
| `podSecurityContext.runAsUser` | User ID for the pod | `999` |
| `podSecurityContext.runAsNonRoot` | Run as non-root user | `true` |
| `securityContext.capabilities.drop` | Linux capabilities to drop | `["ALL"]` |
| `securityContext.readOnlyRootFilesystem` | Mount root filesystem as read-only | `false` |
| `securityContext.allowPrivilegeEscalation` | Allow privilege escalation | `false` |

### PostgreSQL Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.maxConnections` | Maximum number of connections | `100` |
| `postgresql.sharedBuffers` | Shared buffer size | `256MB` |

### Additional Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nodeSelector` | Node labels for pod assignment | `{}` |
| `tolerations` | Tolerations for pod assignment | `[]` |
| `affinity` | Affinity rules for pod assignment | `{}` |
| `podAnnotations` | Annotations for pods | `{}` |
| `extraEnvVars` | Extra environment variables | `[]` |
| `extraVolumeMounts` | Extra volume mounts | `[]` |
| `extraVolumes` | Extra volumes | `[]` |
| `serviceAccount.create` | Create service account | `false` |
| `serviceAccount.name` | Service account name | `""` |
| `serviceAccount.annotations` | Service account annotations | `{}` |

## Examples

### Using External Secret

If you have an existing secret with database credentials:

```yaml
auth:
  existingSecret: "my-existing-secret"
  database: "litellm"
  username: "llmproxy"
```

The secret should contain:
- `username`: Base64 encoded username
- `password`: Base64 encoded password

### Production Configuration

For production environments, consider:

```yaml
# Disable hostPath and use dynamic provisioning
persistence:
  enabled: true
  size: 50Gi
  storageClassName: "fast-ssd"
  hostPath:
    enabled: false

# Increase resources
resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

# Use secure passwords
auth:
  existingSecret: "litellm-db-credentials"

# PostgreSQL tuning
postgresql:
  maxConnections: 200
  sharedBuffers: "1GB"
```

### Development Configuration

For local development:

```yaml
# Use NodePort for external access
service:
  type: NodePort
  nodePort: 30432

# Minimal resources
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

## Integration with LiteLLM

This chart is designed to work seamlessly with LiteLLM. The connection string for LiteLLM would be:

```
postgresql://llmproxy:litellmpassword@litellm-db:5432/litellm
```

When deployed in the same namespace, LiteLLM can connect using the service name.

## Backup and Restore

### Backup

To create a backup of the database:

```bash
kubectl exec -it <pod-name> -- pg_dump -U llmproxy litellm > backup.sql
```

### Restore

To restore from a backup:

```bash
kubectl exec -i <pod-name> -- psql -U llmproxy litellm < backup.sql
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app.kubernetes.io/name=litellm-db-chart
```

### View Logs

```bash
kubectl logs -l app.kubernetes.io/name=litellm-db-chart
```

### Connect to Database

```bash
kubectl exec -it <pod-name> -- psql -U llmproxy -d litellm
```

### Common Issues

1. **Pod stuck in Pending state**: Check PVC status and ensure storage class exists
2. **Connection refused**: Verify service is running and credentials are correct
3. **Permission denied**: Check security contexts and file permissions


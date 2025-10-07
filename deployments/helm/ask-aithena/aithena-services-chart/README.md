# Aithena Services Helm Chart

This Helm chart deploys the Aithena Services application on a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PostgreSQL database (configured separately)

## Installation

### Add the repository (if hosted)

```bash
helm repo add aithena https://github.com/camilovelezr/aithena
helm repo update
```

### Install the chart

```bash
# Install with default values
mk helm install aithena-services ./aithena-services-chart --namespace box

# Install with custom values file
mk helm install aithena-services ./aithena-services-chart -f my-values.yaml --namespace box

# Install with inline value overrides
mk helm install aithena-services ./aithena-services-chart \
  --set postgres.host=my-postgres-host \
  --set secret.postgresPassword=$(echo -n "mypassword" | base64) \
  --namespace box
```

## Uninstallation

```bash
mk helm uninstall aithena-services --namespace box
```

## Configuration

The following table lists the configurable parameters of the Aithena Services chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `camilovelezr/aithena-services` |
| `image.tag` | Image tag | `1.1.2` |
| `image.pullPolicy` | Image pull policy | `Always` |
| `imagePullSecrets` | Image pull secrets | `[]` |
| `namespace` | Namespace (optional, overridden by parent chart) | `""` |
| **Service** | | |
| `service.type` | Service type | `NodePort` |
| `service.port` | Service port | `8000` |
| `service.targetPort` | Target port | `8000` |
| `service.nodePort` | Node port (if type is NodePort) | `32103` |
| `service.name` | Service port name | `http` |
| **PostgreSQL** | | |
| `postgres.host` | PostgreSQL host | `askaithena-db` |
| `postgres.port` | PostgreSQL port | `5432` |
| `postgres.user` | PostgreSQL user | `AithenaAdmin` |
| `postgres.database` | PostgreSQL database | `askaithena` |
| **Secret** | | |
| `secret.existingSecret` | Use existing secret (name) | `""` |
| `secret.postgresPassword` | PostgreSQL password (base64 encoded) | `YmFzZTY0X2VuY29kZWRfcGFzc3dvcmQ=` |
| **Health Probes** | | |
| `probes.readiness.enabled` | Enable readiness probe | `true` |
| `probes.readiness.httpGet.path` | Readiness probe path | `/health` |
| `probes.readiness.httpGet.port` | Readiness probe port | `8000` |
| `probes.readiness.initialDelaySeconds` | Initial delay | `10` |
| `probes.readiness.periodSeconds` | Period | `15` |
| `probes.liveness.enabled` | Enable liveness probe | `true` |
| `probes.liveness.httpGet.path` | Liveness probe path | `/health` |
| `probes.liveness.httpGet.port` | Liveness probe port | `8000` |
| `probes.liveness.initialDelaySeconds` | Initial delay | `30` |
| `probes.liveness.periodSeconds` | Period | `30` |
| **Resources** | | |
| `resources` | CPU/Memory resource requests/limits | `{}` |
| `nodeSelector` | Node selector | `{}` |
| `tolerations` | Tolerations | `[]` |
| `affinity` | Affinity | `{}` |
| `podAnnotations` | Pod annotations | `{}` |
| `podSecurityContext` | Pod security context | `{}` |
| `securityContext` | Container security context | `{}` |
| **Additional** | | |
| `commonLabels` | Labels to add to all resources | `{}` |
| `commonAnnotations` | Annotations to add to all resources | `{}` |
| `extraEnvVars` | Extra environment variables | `[]` |
| `extraVolumeMounts` | Extra volume mounts | `[]` |
| `extraVolumes` | Extra volumes | `[]` |
| `serviceAccount.create` | Create service account | `false` |
| `serviceAccount.annotations` | Service account annotations | `{}` |
| `serviceAccount.name` | Service account name | `""` |
| `autoscaling.enabled` | Enable autoscaling | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `3` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU utilization | `80` |

## Examples

### Using an existing secret

If you already have a Kubernetes secret with the PostgreSQL password:

```yaml
# values.yaml
secret:
  existingSecret: my-existing-secret  # Secret must contain 'postgres_password' key
```

### Custom PostgreSQL configuration

```yaml
# values.yaml
postgres:
  host: my-postgres.example.com
  port: 5432
  user: myuser
  database: mydatabase

secret:
  postgresPassword: "bXlzZWN1cmVwYXNzd29yZA=="  # base64 encoded password
```

### Resource limits

```yaml
# values.yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi
```

### Extra environment variables

```yaml
# values.yaml
extraEnvVars:
  - name: LOG_LEVEL
    value: "DEBUG"
  - name: CUSTOM_CONFIG
    value: "custom-value"
```

## Security Considerations

1. **PostgreSQL Password**: The default password is for demonstration only. Always use a secure password in production:
   ```bash
   # Generate base64 encoded password
   echo -n "your-secure-password" | base64
   ```

2. **Network Policies**: Consider implementing network policies to restrict traffic to/from the service.

3. **Pod Security**: Use appropriate security contexts:
   ```yaml
   podSecurityContext:
     runAsNonRoot: true
     runAsUser: 1000
     fsGroup: 2000
   
   securityContext:
     allowPrivilegeEscalation: false
     capabilities:
       drop:
       - ALL
     readOnlyRootFilesystem: true
   ```

## Troubleshooting

### Check pod status
```bash
mkk get pods -l app.kubernetes.io/name=aithena-services-chart -n box
```

### View logs
```bash
mkk logs -l app.kubernetes.io/name=aithena-services-chart -n box
```

### Describe pod for events
```bash
mkk describe pod -l app.kubernetes.io/name=aithena-services-chart -n box
```

### Test health endpoint
```bash
# Port forward to test locally
mkk port-forward svc/aithena-services-service 8000:8000 -n box
curl http://localhost:8000/health
```

## Integration with Parent Chart

This chart is designed to be used as a subchart in the parent `ask-aithena-chart`. When used as a subchart:

1. The namespace will be managed by the parent chart
2. The parent chart can override any values
3. Dependencies like PostgreSQL should be configured at the parent level

Example parent chart configuration:

```yaml
# parent-chart/values.yaml
aithena-services:
  postgres:
    host: askaithena-db
    port: 5432
  secret:
    existingSecret: shared-postgres-secret
```

## Contributing

Please refer to the main project repository for contribution guidelines.

## License

See the LICENSE file in the main project repository.

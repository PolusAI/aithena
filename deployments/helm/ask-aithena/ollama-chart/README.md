# Ollama Helm Chart

This Helm chart deploys Ollama, a large language model serving platform, on a Kubernetes cluster with GPU support.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- GPU nodes with NVIDIA drivers installed
- PersistentVolume provisioner support (or manual PV creation)

## Installation

### Add the chart repository (if published)
```bash
# If published to a repository
helm repo add ollama-repo <REPO_URL>
helm repo update
```

### Install the chart
```bash
# Install with default values
helm install ollama ./ollama-chart --namespace box

# Install with custom values
helm install ollama ./ollama-chart \
  --namespace box \
  --set replicaCount=2 \
  --set resources.gpu.count=4
```

## Configuration

The following table lists the configurable parameters and their default values:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas in StatefulSet | `1` |
| `image.repository` | Ollama image repository | `ollama/ollama` |
| `image.tag` | Ollama image tag | `0.11.10` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `resources.gpu.count` | Number of GPUs per pod | `2` |
| `resources.limits` | CPU/Memory resource limits | `{}` |
| `resources.requests` | CPU/Memory resource requests | `{}` |
| `storage.enabled` | Enable persistent storage | `true` |
| `storage.size` | Storage size | `250Gi` |
| `storage.storageClassName` | Storage class name | `standard` |
| `storage.accessMode` | PVC access mode | `ReadWriteMany` |
| `storage.hostPath.path` | Host path for storage | `/polus2/velezramirezc2/.data/ollama_data` |
| `storage.reclaimPolicy` | PV reclaim policy | `Retain` |
| `service.type` | Service type | `NodePort` |
| `service.port` | Service port | `11434` |
| `service.nodePort` | NodePort number | `32141` |
| `env.debug` | Enable debug mode | `"1"` |
| `env.flashAttention` | Enable flash attention | `"1"` |
| `probes.readiness.enabled` | Enable readiness probe | `true` |
| `probes.liveness.enabled` | Enable liveness probe | `true` |

### Custom values file

Create a `custom-values.yaml`:

```yaml
replicaCount: 2

resources:
  gpu:
    count: 4
  limits:
    cpu: 4000m
    memory: 16Gi
  requests:
    cpu: 2000m
    memory: 8Gi

storage:
  size: 500Gi

env:
  debug: "0"
  flashAttention: "1"
  schedSpread: "0"
```

Install with custom values:
```bash
helm install ollama ./ollama-chart -f custom-values.yaml --namespace box
```

## Upgrading

```bash
helm upgrade ollama ./ollama-chart --namespace box
```

## Uninstalling

```bash
helm uninstall ollama --namespace box
```

Note: PersistentVolume will be retained due to `Retain` reclaim policy.

## Architecture

This chart deploys:
1. **StatefulSet**: Manages Ollama pods with stable network identities
2. **PersistentVolume**: Provides storage for model data (hostPath)
3. **PersistentVolumeClaim**: Claims the storage for pods
4. **Service**: NodePort service for external access
5. **Headless Service**: For StatefulSet pod DNS resolution

## Multi-Replica Setup

When running multiple replicas, each pod can be accessed via:
```
<release-name>-ollama-chart-<ordinal>.<release-name>-ollama-chart-headless-service.<namespace>.svc.cluster.local
```

For example, with release name `ollama` and namespace `box`:
- `ollama-ollama-chart-0.ollama-ollama-chart-headless-service.box.svc.cluster.local`
- `ollama-ollama-chart-1.ollama-ollama-chart-headless-service.box.svc.cluster.local`

## Testing

### Dry-run installation
```bash
helm install --debug --dry-run ollama ./ollama-chart --namespace box
```

### Test Ollama API
```bash
# Get the NodePort
export NODE_PORT=$(kubectl get --namespace box -o jsonpath="{.spec.ports[0].nodePort}" services ollama-ollama-chart-service)
export NODE_IP=$(kubectl get nodes --namespace box -o jsonpath="{.items[0].status.addresses[0].address}")

# Test the API
curl http://$NODE_IP:$NODE_PORT/api/tags
```

## Troubleshooting

### Check pod status
```bash
kubectl get pods -n box -l "app.kubernetes.io/name=ollama-chart"
```

### View logs
```bash
kubectl logs -n box -l "app.kubernetes.io/name=ollama-chart" -f
```

### Describe StatefulSet
```bash
kubectl describe statefulset -n box ollama-ollama-chart
```

### Check GPU allocation
```bash
kubectl describe nodes | grep -A 5 "Allocated resources"
```

## Notes

- All replicas share the same storage directory (`ReadWriteMany`)
- GPU resources are required and configurable
- The chart is designed to work with the parent "ask-aithena" chart
- Namespace creation is handled by the parent chart

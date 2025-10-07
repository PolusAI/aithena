# Ask AiThena Agent Helm Chart

This Helm chart deploys the Ask AiThena Agent, an AI-powered research assistant, on a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.8.0+
- PV provisioner support in the underlying infrastructure (for persistence)
- Access to the following services:
  - LiteLLM service
  - RabbitMQ service
  - Redis service
  - Arctic service

## Installation

### Add the repository (if using a Helm repository)

```bash
helm repo add aithena https://your-helm-repo.com
helm repo update
```

### Install the chart

```bash
# Install with default values
mk helm install ask-aithena-agent ./deployments/helm/ask-aithena-agent-chart

# Install with custom values
mk helm install ask-aithena-agent ./deployments/helm/ask-aithena-agent-chart \
  --namespace box \
  --create-namespace \
  --set image.tag=1.1.2 \
  --set secret.litellmApiKey="your-actual-api-key"

# Install with values file
mk helm install ask-aithena-agent ./deployments/helm/ask-aithena-agent-chart \
  -f custom-values.yaml
```

## Upgrading

```bash
mk helm upgrade ask-aithena-agent ./deployments/helm/ask-aithena-agent-chart
```

## Uninstallation

```bash
mk helm uninstall ask-aithena-agent
```

## Configuration

The following table lists the configurable parameters of the Ask AiThena Agent chart and their default values.

### General Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `namespace` | Namespace to deploy to (empty means use release namespace) | `""` |

### Image Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Image repository | `camilovelezr/ask-aithena-agent` |
| `image.tag` | Image tag | `1.1.2` |
| `image.pullPolicy` | Image pull policy | `Always` |

### Service Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Service type | `NodePort` |
| `service.port` | Service port | `8000` |
| `service.targetPort` | Target port | `8000` |
| `service.nodePort` | NodePort (if service type is NodePort) | `32105` |
| `service.name` | Service port name | `http` |

### Persistence Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistence | `true` |
| `persistence.storageClassName` | Storage class name | `standard` |
| `persistence.accessMode` | Access mode | `ReadOnlyMany` |
| `persistence.size` | Storage size | `0.5Gi` |
| `persistence.hostPath` | Host path for the volume | `/polus2/velezramirezc2/.data/prompts` |
| `persistence.mountPath` | Mount path in container | `/opt/prompts` |

### Secret Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `secret.existingSecret` | Name of existing secret to use | `""` |
| `secret.litellmApiKeyName` | Key name in secret for API key | `litellm_api_key` |
| `secret.litellmApiKey` | LiteLLM API key (if not using existing secret) | `sk-C` |

### Environment Variables

#### LiteLLM Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `env.litellm.url` | LiteLLM service URL | `http://litellm-service:4000/v1` |
| `env.litellm.useLogfire` | Enable Logfire | `false` |

#### Model Configurations

| Parameter | Description | Default |
|-----------|-------------|---------|
| `env.models.responder.model` | Responder model | `gpt-5` |
| `env.models.responder.temperature` | Responder temperature | `0.5` |
| `env.models.talker.model` | Talker model | `gpt-5` |
| `env.models.talker.temperature` | Talker temperature | `0.85` |
| `env.models.semantics.model` | Semantics model | `gpt-5` |
| `env.models.semantics.temperature` | Semantics temperature | `0.4` |
| `env.models.aegisOrchestrator.model` | AEGIS Orchestrator model | `gpt-5` |
| `env.models.aegisOrchestrator.temperature` | AEGIS Orchestrator temperature | `0.8` |
| `env.models.aegisReferee.model` | AEGIS Referee model | `gpt-5` |
| `env.models.aegisReferee.temperature` | AEGIS Referee temperature | `1` |
| `env.models.shield.model` | Shield model | `gpt-5` |
| `env.models.shield.temperature` | Shield temperature | `0.78` |

#### External Services

| Parameter | Description | Default |
|-----------|-------------|---------|
| `env.rabbitmq.url` | RabbitMQ URL | `amqp://guest:guest@rabbitmq-service:5672/` |
| `env.redis.url` | Redis URL | `redis://redis-service:6379` |
| `env.redis.sessionExpirationSeconds` | Session expiration time | `3600` |
| `env.arctic.host` | Arctic service host | `arctic-direct-0-svc` |
| `env.arctic.port` | Arctic service port | `8000` |

### Health Probes

| Parameter | Description | Default |
|-----------|-------------|---------|
| `probes.readiness.enabled` | Enable readiness probe | `true` |
| `probes.readiness.initialDelaySeconds` | Initial delay for readiness | `10` |
| `probes.readiness.periodSeconds` | Period for readiness check | `15` |
| `probes.liveness.enabled` | Enable liveness probe | `true` |
| `probes.liveness.initialDelaySeconds` | Initial delay for liveness | `30` |
| `probes.liveness.periodSeconds` | Period for liveness check | `30` |

### Resource Limits

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources` | CPU/Memory resource requests/limits | `{}` |

### Autoscaling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `5` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU utilization | `80` |

## Custom Values Example

Create a `custom-values.yaml`:

```yaml
replicaCount: 2

image:
  tag: "1.2.0"

service:
  type: ClusterIP

secret:
  litellmApiKey: "your-real-api-key-here"

env:
  models:
    responder:
      model: "gpt-4"
      temperature: "0.7"
  redis:
    sessionExpirationSeconds: "7200"

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
```

## As a Subchart

This chart can be used as a subchart in a parent chart. In your parent chart's `Chart.yaml`:

```yaml
dependencies:
  - name: ask-aithena-agent-chart
    version: "0.1.0"
    repository: "file://../ask-aithena-agent-chart"
```

Then in your parent chart's `values.yaml`:

```yaml
ask-aithena-agent-chart:
  namespace: box
  secret:
    existingSecret: "my-existing-secret"
  env:
    litellm:
      url: "http://my-litellm:4000/v1"
```

## Troubleshooting

### Check deployment status
```bash
mkk get deployment -n box
mkk describe deployment ask-aithena-agent -n box
```

### View logs
```bash
mkk logs -f deployment/ask-aithena-agent -n box
```

### Check PVC binding
```bash
mkk get pvc -n box
mkk get pv
```

### Test health endpoint
```bash
mkk port-forward deployment/ask-aithena-agent 8000:8000 -n box
curl http://localhost:8000/health
```

## Development

### Lint the chart
```bash
mk helm lint ./deployments/helm/ask-aithena-agent-chart
```

### Dry run installation
```bash
mk helm install ask-aithena-agent ./deployments/helm/ask-aithena-agent-chart \
  --dry-run --debug
```

### Template rendering
```bash
mk helm template ask-aithena-agent ./deployments/helm/ask-aithena-agent-chart
```

## License

This chart is part of the AiThena project. See the main project repository for license information.

## Support

For issues and questions, please open an issue in the [AiThena repository](https://github.com/camilovelezr/aithena).

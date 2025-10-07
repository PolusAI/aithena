# Ask Aithena App Helm Chart

This Helm chart deploys the Ask Aithena application on a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure (if persistence is required)

## Installing the Chart

To install the chart with the release name `ask-aithena-app`:

```bash
mk helm install ask-aithena-app ./deployments/helm/ask-aithena-app-chart
```

## Uninstalling the Chart

To uninstall/delete the `ask-aithena-app` deployment:

```bash
mk helm uninstall ask-aithena-app
```

## Configuration

The following table lists the configurable parameters of the Ask Aithena App chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `2` |
| `image.repository` | Image repository | `camilovelezr/ask-aithena-app` |
| `image.pullPolicy` | Image pull policy | `Always` |
| `image.tag` | Image tag (overrides chart appVersion) | `1.1.4` |
| `imagePullSecrets` | Docker registry secret names | `[]` |
| `nameOverride` | Override chart name | `""` |
| `fullnameOverride` | Override full chart name | `""` |
| **Service** |
| `service.type` | Service type | `NodePort` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Target port | `3000` |
| `service.nodePort` | NodePort (if service type is NodePort) | `32106` |
| `service.protocol` | Service protocol | `TCP` |
| `service.name` | Service name | `http` |
| **Application Configuration** |
| `config.appEnv` | Application environment | `production` |
| `config.apiUrl` | Internal API URL | `http://ask-aithena-agent-service:8000` |
| `config.rabbitmqWsUrl` | Internal RabbitMQ WebSocket URL | `ws://rabbitmq-service:15674/ws` |
| `config.nextPublicApiUrl` | Public API URL | `/api` |
| `config.nextPublicRabbitmqWsUrl` | Public RabbitMQ WebSocket URL | `/askaithena/rabbitmq/ws` |
| `config.extraEnvVars` | Additional environment variables | `[]` |
| **Resources** |
| `resources.limits.cpu` | CPU limit | `1` |
| `resources.limits.memory` | Memory limit | `1Gi` |
| `resources.requests.cpu` | CPU request | `0.3` |
| `resources.requests.memory` | Memory request | `512Mi` |
| **Autoscaling** |
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `2` |
| `autoscaling.maxReplicas` | Maximum replicas | `5` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU utilization | `70` |
| `autoscaling.targetMemoryUtilizationPercentage` | Target memory utilization | `80` |
| **Probes** |
| `probes.liveness.enabled` | Enable liveness probe | `true` |
| `probes.liveness.httpGet.path` | Liveness probe path | `/` |
| `probes.liveness.httpGet.port` | Liveness probe port | `3000` |
| `probes.liveness.initialDelaySeconds` | Initial delay for liveness probe | `30` |
| `probes.liveness.periodSeconds` | Period for liveness probe | `10` |
| `probes.readiness.enabled` | Enable readiness probe | `true` |
| `probes.readiness.httpGet.path` | Readiness probe path | `/` |
| `probes.readiness.httpGet.port` | Readiness probe port | `3000` |
| `probes.readiness.initialDelaySeconds` | Initial delay for readiness probe | `5` |
| `probes.readiness.periodSeconds` | Period for readiness probe | `5` |
| **Pod Configuration** |
| `podAnnotations` | Pod annotations | `{}` |
| `podSecurityContext` | Pod security context | `{}` |
| `securityContext` | Container security context | `{}` |
| `nodeSelector` | Node labels for pod assignment | `{}` |
| `tolerations` | Tolerations for pod assignment | `[]` |
| `affinity` | Affinity for pod assignment | `{}` |
| **ServiceAccount** |
| `serviceAccount.create` | Create service account | `false` |
| `serviceAccount.annotations` | Service account annotations | `{}` |
| `serviceAccount.name` | Service account name | `""` |
| **Additional Volumes** |
| `extraVolumeMounts` | Additional volume mounts | `[]` |
| `extraVolumes` | Additional volumes | `[]` |

### Specify values using YAML file

Create a `values.yaml` file with your custom values:

```yaml
replicaCount: 3

image:
  tag: "1.2.0"

config:
  appEnv: staging
  apiUrl: http://my-custom-api:8000

resources:
  limits:
    cpu: 2
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi
```

Then install the chart with:

```bash
mk helm install ask-aithena-app ./deployments/helm/ask-aithena-app-chart -f values.yaml
```

### Override values using --set

You can also override values during installation:

```bash
mk helm install ask-aithena-app ./deployments/helm/ask-aithena-app-chart \
  --set replicaCount=3 \
  --set image.tag=1.2.0 \
  --set config.appEnv=staging
```

## Testing the Chart

To test the chart without actually installing it:

```bash
mk helm install ask-aithena-app ./deployments/helm/ask-aithena-app-chart --dry-run --debug
```

## Upgrading the Chart

To upgrade an existing release:

```bash
mk helm upgrade ask-aithena-app ./deployments/helm/ask-aithena-app-chart
```

## Notes

- This chart is designed to be used as a subchart of a parent chart that creates the namespace
- The service is configured as NodePort by default for development environments
- Autoscaling is enabled by default with min 2 and max 5 replicas
- The application expects certain services to be available (ask-aithena-agent-service, rabbitmq-service)

## Troubleshooting

### Check pod status
```bash
mkk get pods -l app.kubernetes.io/name=ask-aithena-app-chart
```

### View logs
```bash
mkk logs -l app.kubernetes.io/name=ask-aithena-app-chart -f
```

### Describe deployment
```bash
mkk describe deployment <release-name>-ask-aithena-app-chart
```

### Check HPA status
```bash
mkk get hpa <release-name>-ask-aithena-app-chart-hpa
```

## License

This chart is licensed under the Apache 2.0 License.

# RabbitMQ Helm Chart

This Helm chart provides a simple and efficient way to deploy RabbitMQ to a Kubernetes cluster. It is designed to be easily configurable and follows Helm best practices.

## Overview

This chart deploys RabbitMQ with the following features:
-   **RabbitMQ with Management Plugin:** Includes the RabbitMQ Management UI for easy administration.
-   **Web STOMP Plugin:** Enables messaging over WebSockets.
-   **Configurable Services:** Supports both internal `ClusterIP` services and external `NodePort` services.
-   **Flexible Configuration:** All major settings can be configured through `values.yaml`.
-   **Resource Management:** Allows specifying resource requests and limits.
-   **Health Checks:** Includes liveness and readiness probes for robust monitoring.

## Prerequisites

-   Kubernetes 1.19+
-   Helm 3.2.0+

## Installation

To install the chart with the release name `my-rabbitmq`:

```bash
mk helm install my-rabbitmq ./rabbitmq-chart
```

This command deploys RabbitMQ on the Kubernetes cluster in the default configuration.

## Configuration

The following table lists the configurable parameters of the RabbitMQ chart and their default values.

| Parameter                  | Description                                     | Default                               |
| -------------------------- | ----------------------------------------------- | ------------------------------------- |
| `replicaCount`             | Number of RabbitMQ replicas                     | `1`                                   |
| `image.repository`         | RabbitMQ image repository                       | `rabbitmq`                            |
| `image.pullPolicy`         | Image pull policy                               | `IfNotPresent`                        |
| `image.tag`                | RabbitMQ image tag                              | `"4.1.2-management"`                  |
| `rabbitmq.defaultUser`     | Default RabbitMQ username                       | `guest`                               |
| `rabbitmq.defaultPass`     | Default RabbitMQ password                       | `guest`                               |
| `rabbitmq.hostname`        | Hostname for the RabbitMQ node                  | `my-rabbit`                           |
| `rabbitmq.plugins`         | List of plugins to enable                       | `[rabbitmq_management, rabbitmq_web_stomp]` |
| `service.internal.type`    | Type of internal service                        | `ClusterIP`                           |
| `service.external.enabled` | Enable external NodePort service for STOMP      | `true`                                |
| `service.management.enabled`| Enable external NodePort service for Management | `true`                                |
| `resources`                | CPU/Memory resource requests/limits             | `{}`                                  |
| `persistence.enabled`      | Enable persistence using PVCs                   | `false`                               |

Specify each parameter using the `--set key=value[,key=value]` argument to `mk helm install`. For example:

```bash
mk helm install my-rabbitmq ./rabbitmq-chart --set rabbitmq.defaultUser=admin --set rabbitmq.defaultPass=secret
```

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example:

```bash
mk helm install my-rabbitmq ./rabbitmq-chart -f values.yaml
```

## Uninstallation

To uninstall/delete the `my-rabbitmq` deployment:

```bash
mk helm uninstall my-rabbitmq
```

This command removes all the Kubernetes components associated with the chart and deletes the release.

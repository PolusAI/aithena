# RabbitMQ Deployment

This directory contains the deployment for RabbitMQ.

## Description
RabbitMQ serves as the message broker for real-time communication between the Agent and the UI.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.

### 1. Edit environment variables in the deployment.yaml file

Edit the `deployment.yaml` file with your credentials:
- `RABBITMQ_DEFAULT_USER`: The admin username (default: guest).
- `RABBITMQ_DEFAULT_PASS`: The admin password (default: guest).
- `HOSTNAME`: The hostname for the node.

*Note: For production, it is recommended to move these credentials to a Secret.*

## Deployment

Apply the configuration map, deployment, and services:

```bash
# Apply ConfigMap (Plugins)
microk8s kubectl apply -f configmap.yaml

# Apply Deployment
microk8s kubectl apply -f deployment.yaml

# Apply Services (Internal, External, Management)
microk8s kubectl apply -f service_internal.yaml
microk8s kubectl apply -f service_external.yaml
microk8s kubectl apply -f service_management.yaml
```

## Verification
Check if the pods are running:
```bash
microk8s kubectl -n box get pods -l app=rabbitmq
```

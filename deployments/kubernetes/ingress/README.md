# Ingress Configuration

This directory contains the Ingress resources for AskAithena.

## Description
Ingress handles external access to the services in the cluster, such as the main web app and the RabbitMQ websocket connection.

## Prerequisites
- **Ingress Controller**: Ensure the NGINX ingress controller is enabled in MicroK8s:
  ```bash
  microk8s enable ingress
  ```

### 1. Edit Hostnames in Ingress Files

Edit `aithena-ingress.yaml` and `rabbitmq-websocket-ingress.yaml`:
- `host`: Change to your actual domain name (e.g., `aithena.example.com`).

## Deployment

Apply the ingress rules:

```bash
# Main application ingress
microk8s kubectl apply -f aithena-ingress.yaml

# RabbitMQ Websocket ingress
microk8s kubectl apply -f rabbitmq-websocket-ingress.yaml
```

## Verification
Check the ingress status:
```bash
microk8s kubectl -n box get ingress
```

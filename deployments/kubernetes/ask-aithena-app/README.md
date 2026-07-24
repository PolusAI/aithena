# Ask Aithena App Deployment

This directory contains the Kubernetes deployment for the AskAithena Web UI.

## Description
`ask-aithena-app` is the web-based user interface that allows users to submit queries and view real-time responses.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.

### 1. Edit Configuration
The application uses a ConfigMap for configuration instead of secrets.

Edit `configmap.yaml` with your specific settings if needed (e.g., public URLs).

### 2. Edit environment variables in the deployment.yaml file
If you need to override values not in the ConfigMap, edit the `deployment.yaml` file.

- `NEXT_PUBLIC_API_URL`: The URL for the backend API (if client-side).
- `NEXT_PUBLIC_WS_URL`: The WebSocket URL for real-time updates.

## Deployment

This directory uses `kustomize` to manage configuration.

To deploy all resources (Deployment, Service, ConfigMap, HPA):

```bash
microk8s kubectl apply -k .
```

## Verification
Check if the application is running:
```bash
microk8s kubectl -n box get pods -l app=ask-aithena-app
```

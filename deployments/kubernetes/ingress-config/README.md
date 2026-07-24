# Ingress Config Customization

This directory contains configuration customizations for the NGINX Ingress Controller.

## Description
The ConfigMap `nginx-timeouts-configmap.yaml` adjusts timeout settings for the ingress controller to support long-running connections (e.g., for LLM streaming responses).

## Prerequisites
- **Namespace**: Ensure the `ingress` namespace exists (created by `microk8s enable ingress`).

### 1. Edit Configuration
Edit `nginx-timeouts-configmap.yaml` if you need to adjust specific timeout values:
- `proxy-read-timeout`
- `proxy-send-timeout`

## Deployment

**Note**: This resource belongs to the `ingress` namespace, not the `box` namespace used by the rest of the application.

Apply the configuration:

```bash
microk8s kubectl apply -f nginx-timeouts-configmap.yaml
```

## Verification
Check if the configmap exists in the ingress namespace:
```bash
microk8s kubectl -n ingress get configmap nginx-load-balancer-microk8s-conf
```

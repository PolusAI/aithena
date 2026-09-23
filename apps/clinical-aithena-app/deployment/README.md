# Clinical Aithena UI Deployment

This directory contains Kubernetes deployment configurations for the Clinical Aithena web application (Next.js React UI).

## Overview

The Clinical Aithena UI is a Next.js application that provides a modern web interface for interacting with the Clinical Aithena API. It is designed to be deployed on Kubernetes using microk8s.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│                                                              │
│  ┌──────────────┐                                           │
│  │   Ingress    │ (polus1.ncats.nih.gov/gardian)           │
│  │  (TLS/HTTPS) │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│  ┌──────▼───────┐                                           │
│  │  UI Service  │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│  ┌──────▼────────────────┐                                 │
│  │  UI Pods (x2)         │                                 │
│  │  - Next.js Server     │                                 │
│  │  - React Frontend     │                                 │
│  │  - Port 3000          │                                 │
│  └──────┬────────────────┘                                 │
│         │                                                    │
│         │ Calls API at:                                     │
│         │ https://polus1.ncats.nih.gov/apis/ctaithena     │
│         │                                                    │
│  ┌──────▼────────────────┐                                 │
│  │  API Service          │                                 │
│  │  (FastAPI Backend)    │                                 │
│  └───────────────────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
deployment/
├── README.md                  # This file
├── ui-deployment.yaml         # Kubernetes Deployment
├── ui-service.yaml            # Kubernetes Service
├── ui-ingress.yaml            # Ingress for external access
├── ui-config.yaml             # ConfigMap for environment variables
├── deploy-ui.sh               # Deployment script
└── cleanup-ui.sh              # Cleanup script
```

## Prerequisites

1. **Kubernetes Cluster**: Access to a microk8s cluster
2. **Namespace**: The `clinical-aithena` namespace should exist
3. **Docker Image**: The UI Docker image should be built and available
4. **API**: The Clinical Aithena API should be deployed and accessible
5. **TLS Certificate**: The `polus1-tls` secret should exist in the namespace for HTTPS

### Check Prerequisites

```bash
# Check if microk8s is available
microk8s kubectl version

# Check if namespace exists
microk8s kubectl get namespace clinical-aithena

# Check if TLS secret exists
microk8s kubectl -n clinical-aithena get secret polus1-tls

# Check if API is running
microk8s kubectl -n clinical-aithena get pods -l app=clinical-aithena-api
```

## Building the Docker Image

Before deploying, you need to build the Docker image for the UI application.

### 1. Build the Image

From the app root directory:

```bash
cd /polus1/schaubnj/clinical-aithena/apps/clinical-aithena-app

# Build the Docker image
docker build -t polusai/ctaithena-ui:latest .
```

The Dockerfile uses a multi-stage build process:
- **Stage 1 (deps)**: Install production dependencies
- **Stage 2 (builder)**: Build the Next.js application
- **Stage 3 (runner)**: Create minimal production image

### 2. Push to Registry (Production)

For production deployments, push the image to a container registry:

```bash
# Tag the image (if needed)
docker tag polusai/ctaithena-ui:latest your-registry.com/polusai/ctaithena-ui:latest

# Push to registry
docker push your-registry.com/polusai/ctaithena-ui:latest

# Update ui-deployment.yaml with the registry path
# Then apply the updated deployment
```

### 3. Local Development with microk8s

For local development with microk8s, you can import the image directly:

```bash
# Save the image to a tar file
docker save polusai/ctaithena-ui:latest > ctaithena-ui.tar

# Import into microk8s
microk8s ctr image import ctaithena-ui.tar

# Verify the image
microk8s ctr images ls | grep ctaithena-ui
```

## Configuration

### Environment Variables

The UI application is configured via the `ui-config.yaml` ConfigMap:

```yaml
NEXT_PUBLIC_API_URL: "https://polus1.ncats.nih.gov/apis/ctaithena"
NODE_ENV: "production"
NEXT_TELEMETRY_DISABLED: "1"
```

To modify the API URL or other settings, edit `ui-config.yaml` before deployment.

### Ingress Configuration

The UI is served at: **https://polus1.ncats.nih.gov/gardian**

The ingress configuration (`ui-ingress.yaml`) includes:
- **Path rewriting**: `/gardian/*` is rewritten to `/*` for the Next.js app
- **TLS/SSL**: Uses the `polus1-tls` secret for HTTPS
- **Timeouts**: Configured for typical web application response times

## Deployment

### Quick Deployment

```bash
cd /polus1/schaubnj/clinical-aithena/apps/clinical-aithena-app/deployment

# Make the deployment script executable
chmod +x deploy-ui.sh

# Run the deployment script
./deploy-ui.sh
```

The script will:
1. Check if microk8s is available
2. Verify the namespace exists (or create it)
3. Check if the Docker image is available
4. Deploy the ConfigMap
5. Deploy the Service
6. Deploy the Deployment
7. Optionally deploy the Ingress

### Manual Deployment

If you prefer to deploy manually:

```bash
KUBECTL="microk8s kubectl"
NAMESPACE="clinical-aithena"

# 1. Create ConfigMap
$KUBECTL apply -f ui-config.yaml

# 2. Create Service
$KUBECTL apply -f ui-service.yaml

# 3. Create Deployment
$KUBECTL apply -f ui-deployment.yaml

# 4. Create Ingress
$KUBECTL apply -f ui-ingress.yaml
```

## Monitoring

### Check Deployment Status

```bash
# Get all UI resources
microk8s kubectl -n clinical-aithena get all -l app=clinical-aithena-ui

# Check pod status
microk8s kubectl -n clinical-aithena get pods -l app=clinical-aithena-ui

# Watch pods in real-time
microk8s kubectl -n clinical-aithena get pods -l app=clinical-aithena-ui -w
```

### View Logs

```bash
# View logs from all UI pods
microk8s kubectl -n clinical-aithena logs -l app=clinical-aithena-ui -f

# View logs from a specific pod
microk8s kubectl -n clinical-aithena logs clinical-aithena-ui-xxxxxxxxxx-xxxxx -f
```

### Check Ingress

```bash
# Get ingress details
microk8s kubectl -n clinical-aithena get ingress clinical-aithena-ui

# Describe ingress (shows events and configuration)
microk8s kubectl -n clinical-aithena describe ingress clinical-aithena-ui
```

## Testing

### Port Forwarding (Local Testing)

```bash
# Forward the service port to localhost
microk8s kubectl -n clinical-aithena port-forward svc/clinical-aithena-ui 3000:80

# Access the UI at:
# http://localhost:3000
```

### External Access

Once the ingress is deployed, access the UI at:
- **Production URL**: https://polus1.ncats.nih.gov/gardian

### Verify API Connection

The UI should automatically connect to the API at:
- **API URL**: https://polus1.ncats.nih.gov/apis/ctaithena

You can verify the connection by:
1. Opening the UI in a browser
2. Checking the browser console for any API errors
3. Testing the search functionality

## Scaling

### Scale Replicas

```bash
# Scale to 3 replicas
microk8s kubectl -n clinical-aithena scale deployment clinical-aithena-ui --replicas=3

# Scale to 1 replica (minimal)
microk8s kubectl -n clinical-aithena scale deployment clinical-aithena-ui --replicas=1
```

Or edit `ui-deployment.yaml` and update the `replicas` field.

## Updating the Deployment

### Update Configuration

```bash
# Edit the ConfigMap
nano ui-config.yaml

# Apply the changes
microk8s kubectl apply -f ui-config.yaml

# Restart pods to pick up the new configuration
microk8s kubectl -n clinical-aithena rollout restart deployment clinical-aithena-ui
```

### Update the Application

```bash
# Build and push new image version
docker build -t polusai/ctaithena-ui:v1.1.0 .
docker push polusai/ctaithena-ui:v1.1.0

# Update the deployment
microk8s kubectl -n clinical-aithena set image deployment/clinical-aithena-ui \
  ui=polusai/ctaithena-ui:v1.1.0

# Check rollout status
microk8s kubectl -n clinical-aithena rollout status deployment/clinical-aithena-ui
```

## Cleanup

To remove all UI resources:

```bash
cd /polus1/schaubnj/clinical-aithena/apps/clinical-aithena-app/deployment

# Make the cleanup script executable
chmod +x cleanup-ui.sh

# Run the cleanup script
./cleanup-ui.sh
```

Or manually:

```bash
microk8s kubectl delete -f ui-ingress.yaml
microk8s kubectl delete -f ui-deployment.yaml
microk8s kubectl delete -f ui-service.yaml
microk8s kubectl delete -f ui-config.yaml
```

## Troubleshooting

### Pods not starting

```bash
# Check pod events
microk8s kubectl -n clinical-aithena describe pod clinical-aithena-ui-xxxxxxxxxx-xxxxx

# Check logs
microk8s kubectl -n clinical-aithena logs clinical-aithena-ui-xxxxxxxxxx-xxxxx
```

Common issues:
- **ImagePullBackOff**: Docker image not available
- **CrashLoopBackOff**: Application error, check logs

### Cannot access UI via ingress

```bash
# Check ingress configuration
microk8s kubectl -n clinical-aithena describe ingress clinical-aithena-ui

# Check if ingress controller is running
microk8s kubectl get pods -n ingress -l app.kubernetes.io/name=ingress-nginx
```

Common issues:
- **404 Not Found**: Check path rewriting in `ui-ingress.yaml`
- **502 Bad Gateway**: UI pods not ready, check pod status
- **503 Service Unavailable**: Service not routing to pods correctly

### UI cannot connect to API

Check the API URL configuration:

```bash
# Get the current configuration
microk8s kubectl -n clinical-aithena get configmap clinical-aithena-ui-config -o yaml

# Verify API is accessible
curl -k https://polus1.ncats.nih.gov/apis/ctaithena/health
```

Update the API URL in `ui-config.yaml` if needed, then:

```bash
microk8s kubectl apply -f ui-config.yaml
microk8s kubectl -n clinical-aithena rollout restart deployment clinical-aithena-ui
```

## Resource Requirements

### Default Resources

- **CPU**: 250m (request), 1 (limit)
- **Memory**: 256Mi (request), 1Gi (limit)
- **Replicas**: 2 (for high availability)

### Adjust Resources

Edit `ui-deployment.yaml` to adjust resource limits based on your needs:

```yaml
resources:
  limits:
    cpu: "2"
    memory: "2Gi"
  requests:
    cpu: "500m"
    memory: "512Mi"
```

## Security

### Security Features

1. **Non-root user**: Containers run as user 1001 (nextjs)
2. **Read-only root filesystem**: Configured for security
3. **Dropped capabilities**: All Linux capabilities dropped
4. **TLS/HTTPS**: Ingress uses TLS certificate
5. **Network policies**: Can be added for additional isolation

### TLS Certificate

The deployment expects a TLS secret named `polus1-tls` to exist in the namespace:

```bash
# Check if the secret exists
microk8s kubectl -n clinical-aithena get secret polus1-tls

# If not, create it (example)
microk8s kubectl -n clinical-aithena create secret tls polus1-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

## Next.js Configuration

### Standalone Output

The Dockerfile is configured to use Next.js standalone output for minimal image size. This is configured in `next.config.ts`:

```typescript
const nextConfig = {
  output: 'standalone',
  // ... other config
};
```

Make sure this is set in your `next.config.ts` before building the Docker image.

### Base Path (Optional)

If you need to serve the app at a specific base path (e.g., `/gardian`), update `next.config.ts`:

```typescript
const nextConfig = {
  output: 'standalone',
  basePath: '/gardian',
  assetPrefix: '/gardian',
};
```

Note: With the current ingress configuration using path rewriting, this is not necessary.

## Support

For issues or questions:
1. Check the logs: `microk8s kubectl -n clinical-aithena logs -l app=clinical-aithena-ui`
2. Review pod status: `microk8s kubectl -n clinical-aithena get pods`
3. Check ingress events: `microk8s kubectl -n clinical-aithena describe ingress clinical-aithena-ui`
4. Verify API connectivity: Test the API endpoint directly

## Related Documentation

- **API Deployment**: `../../agents/clinical-aithena-agent/deployment/api/README.md`
- **Full System Deployment**: `../../agents/clinical-aithena-agent/deployment/README.md`
- **Next.js Documentation**: https://nextjs.org/docs
- **Kubernetes Documentation**: https://kubernetes.io/docs/


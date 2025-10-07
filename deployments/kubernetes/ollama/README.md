# Ollama Kubernetes Setup

This directory contains Kubernetes manifests to deploy Ollama with persistent storage for models, mounting to the standard `/root/.ollama` path used by Ollama.

## Files
- `pv.yaml`: PersistentVolume for Ollama models storage
- `pvc.yaml`: PersistentVolumeClaim that requests storage from the PV
- `deployment.yaml`: Deployment for the Ollama service
- `service.yaml`: Service to expose Ollama within the cluster
- `setup-models.sh`: Helper script to set up the models directory on the host

## Setup Instructions

1. Run the setup script to create the host directory:
   ```bash
   ./setup-models.sh
   ```

2. Apply the Kubernetes resources:
   ```bash
   kubectl apply -f services/aithena-services/kubernetes/ollama/
   ```

3. After deployment is complete, you can pull models:
   ```bash
   kubectl exec -it deployment/ollama -- ollama pull mistral
   ```

## Resource Configuration

The deployment is configured with NO LIMITS:
- No memory requests or limits
- No CPU requests or limits
- Only requesting all available NVIDIA GPUs

This configuration allows Ollama to use all available node resources without restrictions, providing maximum performance for running large language models.

**Note:** For GPU acceleration to work properly, you need to have:
1. NVIDIA GPUs available in your cluster
2. NVIDIA device plugin installed in your Kubernetes cluster

## Model Management

Since the models are stored on a persistent volume at `/data/ollama` on the host, they will persist across pod restarts. Models can be managed using standard Ollama commands:

```bash
# Pull a model
kubectl exec -it deployment/ollama -- ollama pull <model-name>

# List available models
kubectl exec -it deployment/ollama -- ollama list

# Remove a model
kubectl exec -it deployment/ollama -- ollama rm <model-name>
``` 
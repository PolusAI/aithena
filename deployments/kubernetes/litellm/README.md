# LiteLLM Kubernetes Setup

This directory contains Kubernetes manifests to deploy LiteLLM with a configuration file mounted from the host.

## Files
- `pv.yaml`: PersistentVolume for the config file directory
- `pvc.yaml`: PersistentVolumeClaim that requests storage from the PV
- `deployment.yaml`: Deployment for the LiteLLM service
- `service.yaml`: Service to expose LiteLLM within the cluster
- `setup-config.sh`: Helper script to set up the config.yaml on the host

## Setup Instructions

1. Run the setup script to create the host directory and a default config.yaml:
   ```bash
   ./setup-config.sh
   ```

2. Customize the config.yaml file at `/data/litellm-config/config.yaml` as needed.

3. Apply the Kubernetes resources:
   ```bash
   kubectl apply -f services/aithena-services/kubernetes/litellm/
   ```

## Configuration Updates

To update the LiteLLM configuration:
1. Edit the config file directly on the host at `/data/litellm-config/config.yaml`
2. Restart the LiteLLM pod to apply changes:
   ```bash
   kubectl rollout restart deployment litellm
   ```

## Dependencies

This deployment depends on:
- The LiteLLM database (deployed separately)
- An Ollama service (named `ollama-service`)

Make sure these services are deployed before deploying LiteLLM. 
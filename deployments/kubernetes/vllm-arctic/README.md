# vLLM Arctic Deployment

This directory contains the deployment for the Arctic embedding model using vLLM.

## Description
`arctic` is a dedicated vLLM-based server specifically for generating vector embeddings from text. It allows you to load multiple replicas of the same model on each GPU to improve throughput.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.
- **Storage**: You need to create the `arctic-direct-pv` and `arctic-direct-pvc` before deploying.
- **HuggingFace Model**: You need to have the model downloaded and stored in the host filesystem.

### 0. Download the Model
Download the model from HuggingFace:
```bash
hf download Snowflake/snowflake-arctic-embed-l-v2.0
```

### 1. Edit pv.yaml

Edit the pv.yaml file with:
- `hostPath.path`: The path where the model is stored in the host filesystem.

### 1. Edit environment variables and args in the deployment files

Edit `deployment_single.yaml` or `deployment_six.yaml`:
- `--num-replicas`: Number of model replicas per GPU.
- `--model`: Path or ID of the model to load.

## Deployment

Choose the deployment configuration that matches your resource availability.

### Option A: Single Replica (Default/Dev)
Use this for simpler setups or development.

```bash
# Storage
microk8s kubectl apply -f pv.yaml
microk8s kubectl apply -f pvc.yaml

# Deployment
microk8s kubectl apply -f deployment_single.yaml
```

### Option B: High Availability (6 Replicas)
Use this for production environments requiring higher throughput.

```bash
# Storage
microk8s kubectl apply -f pvs.yaml

# Deployment
microk8s kubectl apply -f statefulset_six.yaml
```

### Services
Apply the necessary services:

```bash
microk8s kubectl apply -f service.yaml
microk8s kubectl apply -f service-headless.yaml
```

## Verification
Check if the pods are running:
```bash
microk8s kubectl -n box get pods -l app=arctic-direct
```

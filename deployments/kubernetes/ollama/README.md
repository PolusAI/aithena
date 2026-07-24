# Ollama Deployment

This directory contains Kubernetes manifests to deploy Ollama with persistent storage for models.

## Description
Ollama is used for local inference of Large Language Models (LLMs) like Mistral, Gemma, etc., avoiding external API dependencies for certain tasks.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.
- **Hardware**: NVIDIA GPUs are highly recommended for performance.

## Deployment

## Option A: Single Replica

### 1. Storage

Edit the pv.yaml file with:
- `hostPath.path`: The path where the models are stored in the host filesystem.

### 2. Apply the Persistent Volume and Claim
```bash
microk8s kubectl apply -f pv.yaml
microk8s kubectl apply -f pvc.yaml
```

### 3. Apply the Service and Deployment

```bash
microk8s kubectl apply -f service.yaml
microk8s kubectl apply -f deployment.yaml
```

## Verification
Check if the pods are running:
```bash
microk8s kubectl -n box get pods -l app=ollama
```

## Post-Deployment: Pulling Models

After the pod is running, you need to pull the models you want to use.

```bash
# Pull a model (e.g., mistral)
microk8s kubectl -n box exec -it deployment/ollama -- ollama pull model-name

# List available models
microk8s kubectl -n box exec -it deployment/ollama -- ollama list
```

## Option B: 6 Replicas

### 1. Storage

Edit the pvs.yaml file with:
- `hostPath.path`: The path where the models are stored in the host filesystem.

### 2. Apply the Persistent Volumes and Claims
```bash
microk8s kubectl apply -f pv.yaml
microk8s kubectl apply -f pvc.yaml
```

### 3. Apply the Service and Deployment
```bash
microk8s kubectl apply -f service-headless.yaml
microk8s kubectl apply -f statefulset.yaml
```

(A statefulset needs a headless service to work properly)

### 4. Verify the Deployment
```bash
microk8s kubectl -n box get pods -l app=ollama
```

### 5. Pull the Models
```bash
microk8s kubectl -n box exec -it deployment/ollama -- ollama pull model-name
```

### 6. Optional: Add Load Balancing
You can optionally add a load balancing service to the statefulset.

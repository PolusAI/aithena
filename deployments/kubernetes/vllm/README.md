# vLLM Deployment - This has *NOT* been tested yet. It is a work in progress.

This directory contains the deployment for vLLM 

## Description
vLLM is used for high-performance LLM inference.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.
- **Hardware**: This deployment requires NVIDIA GPUs and the corresponding Kubernetes device plugins.

### 0. Download the Model
Download the model from HuggingFace:
```bash
hf download mistralai/Mistral-Small-3.2-24B-Instruct-2506
```

### 1. Edit Command Arguments in statefulset.yaml

Edit the `statefulset.yaml` file to configure the model:
- `vllm serve [model-name]`: Specify the model you want to serve (e.g., `mistralai/Mistral-Small-3.2-24B-Instruct-2506`).
- `--tensor-parallel-size`: Match this to the number of GPUs requested in `resources`.

## Deployment

1. **Storage**
Apply the Persistent Volume:
```bash
microk8s kubectl apply -f pv.yaml
```

2. **Workload**
Deploy the StatefulSet and Services:
```bash
microk8s kubectl apply -f statefulset.yaml
microk8s kubectl apply -f service-headless.yaml
microk8s kubectl apply -f service-direct.yaml
```

## Verification
Check if the pods are running:
```bash
microk8s kubectl -n box get pods -l app=vllm-nemotron
```

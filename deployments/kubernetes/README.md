# AskAithena Kubernetes Deployment Guide

This directory contains all the Kubernetes manifests required to deploy the AskAithena platform. We use **MicroK8s** as our Kubernetes distribution.

NOTE: We use the `box` namespace as an example for all services. You can use any namespace you want.
```bash
microk8s kubectl create namespace box # or any other namespace you want
```

## Architecture Overview

AskAithena is composed of several microservices working together. Refer to `@diagrams/AskAithena_Structure.md` for a detailed architecture breakdown.

**Core Services:**
- **UI**: `ask-aithena-app`
- **Agent**: `ask-aithena-agent`
- **Data**: `postgres` (with pgvector)
- **Messaging**: `rabbitmq`
- **AI/Inference**: `litellm`, `ollama`, `vllm-arctic` (embeddings), `vllm`

## Prerequisites

1. **MicroK8s Installed**: Ensure MicroK8s is installed and running.
2. **Addons Enabled**:
   ```bash
   microk8s enable dns storage ingress helm
   # If using GPUs:
   microk8s enable gpu
   ```
3. **Namespace**: Create the `box` namespace used by all services.
   ```bash
   microk8s kubectl create namespace box
   ```

## Recommended Deployment Order

Deploy the services in the following order to ensure dependencies are met:

### 1. Data Layer & Infrastructure
Start with the foundational data services.
- **Postgres**: Main database (critical). See [postgres/README.md](./postgres/README.md)
- **RabbitMQ**: Messaging broker. See [rabbitmq/README.md](./rabbitmq/README.md)
- **LiteLLM DB**: Database for AI Gateway. See [litellm_db/README.md](./litellm_db/README.md)

### 2. AI Inference Layer
Deploy the model serving and gateway layers.
- **Ollama**: Local LLM inference. See [ollama/README.md](./ollama/README.md)
- **vLLM / Arctic**: Embedding services. See [vllm-arctic/README.md](./vllm-arctic/README.md)
- **LiteLLM**: AI Gateway (depends on LiteLLM DB and Ollama). See [litellm/README.md](./litellm/README.md)

## Important Note on the Arctic Model

The Arctic embedding service (`vllm-arctic`) and the Ask Aithena Agent (`ask-aithena-agent`) are tightly coupled regarding the embedding model configuration.

**CRITICAL**: The model path defined in the Arctic deployment (via the `--model` argument) **MUST** match exactly the `EMBEDDING_MODEL` environment variable in the Ask Aithena Agent deployment.
- If these values do not match, the agent will request embeddings for a model that the Arctic service does not recognize or has not loaded, causing failures.
- When updating the model in `vllm-arctic`, you **must** also update the `ask-aithena-agent` configuration.

### 3. Backend Logic
Deploy the core application services.
- **Aithena Services**: Core business logic. See [aithena-services/README.md](./aithena-services/README.md)
- **Ask Aithena Agent**: Orchestrator (depends on LiteLLM, RabbitMQ). See [ask-aithena-agent/README.md](./ask-aithena-agent/README.md)

### 4. Frontend & Access
Finally, deploy the UI and expose services.
- **Ask Aithena App**: Web UI. See [ask-aithena-app/README.md](./ask-aithena-app/README.md)
- **Ingress**: External access rules. See [ingress/README.md](./ingress/README.md)

## Common Commands

- **Check all pods in the namespace**:
  ```bash
  microk8s kubectl -n box get pods
  ```

- **View logs for a service**:
  ```bash
  microk8s kubectl -n box logs -f deployment/<deployment-name>
  ```

- **Restart a deployment**:
  ```bash
  microk8s kubectl -n box rollout restart deployment/<deployment-name>
  ```

## Configuration

Most services use **Secrets** for sensitive data (API keys, passwords) and **ConfigMaps** for general configuration. 
- Always look for `secret_sample.yaml` in the service directory to see what credentials are required.
- **Never commit actual secrets to the repository.**

---
*For detailed instructions on each service, please navigate to the respective directory.*


# Ask Aithena Agent Deployment

This directory contains the Kubernetes deployment for the AskAithena Agent.

## Description
`ask-aithena-agent` is the central brain of the system. It hosts agents that orchestrate workflows, process user queries, request embeddings, and generate responses.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.
- **Secrets**: You need to create the `ask-aithena-agent-secret`.

### 1. Create Secret
Copy the sample secret and fill in your actual values:

```bash
cp secret_sample.yaml secret.yaml
```

### 2. Edit the secret
Edit the secret.yaml file with:
- `litellm_api_key`: The API Key for the LiteLLM proxy service.

This needs to be base64 encoded.
```bash
echo -n "your-api-key" | base64
```
Don't forget to include `-n` to echo the password without a newline.

### 3. Apply the secret

Apply the secret:
```bash
microk8s kubectl apply -f secret.yaml
```

### 4. Edit pv.yaml

Edit the pv.yaml file with:
- `hostPath.path`: The path where the prompts are stored in the host filesystem.

### 5. Edit environment variables in the deployment.yaml file

Edit the deployment.yaml file with:
- `LITELLM_URL`: The URL of the LiteLLM service.
- `RABBITMQ_URL`: The connection string for RabbitMQ.
- `EMBEDDING_TABLE`: The table where the embeddings are stored.
- Model Configurations:
    - `RESPONDER_MODEL`
    - `TALKER_MODEL`
    - `SEMANTICS_MODEL`
    - `AEGIS_ORCHESTRATOR_MODEL`
    - `AEGIS_REFEREE_MODEL`
    - `SHIELD_MODEL`
    -  And temperature and other parameters for each model.
- `PROMPTS_DIR`: The directory where the prompts are stored.
- `ARCTIC_HOST`: The host of the Arctic service.
- `ARCTIC_PORT`: The port of the Arctic service.
- `HTTPX_TIMEOUT`: The timeout for HTTP requests.

## Deployment

1. **Persistent Storage**
Apply the Persistent Volume (PV) and Persistent Volume Claim (PVC) to store prompts and other persistent data:

```bash
microk8s kubectl apply -f pv.yaml
microk8s kubectl apply -f pvc.yaml
```

2. **Deploy Service and Agent**

```bash
microk8s kubectl apply -f deployment.yaml
microk8s kubectl apply -f service.yaml
```

## Verification
Check the status of the deployment:
```bash
microk8s kubectl -n box get pods -l app=ask-aithena-agent
```

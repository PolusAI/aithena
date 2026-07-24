# LiteLLM Deployment

This directory contains the Kubernetes deployment for LiteLLM.

## Description
`litellm` acts as a unified API gateway for LLM interactions, abstracting differences between various LLM providers and routing requests.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.
- **Secrets**: You need to create the `litellm-secret`.

### 1. Create Secret
Copy the sample secret and fill in your actual values:

```bash
cp secret_sample.yaml secret.yaml
```

### 2. Edit the secret
Edit the secret.yaml file with:
- `AZURE_API_KEY`: API Key for Azure OpenAI (or other providers).
- `AZURE_API_BASE`: Base URL for the API.

These need to be base64 encoded.
```bash
echo -n "your-value" | base64
```
Don't forget to include `-n` to echo the password without a newline.

### 3. Apply the secret

Apply the secret:
```bash
microk8s kubectl apply -f secret.yaml
```

### 4. Edit pv.yaml

Edit the pv.yaml file with:
- `hostPath.path`: The path where the config is stored in the host filesystem.

**NOTE**: When using Vertex AI, one way to set up the credentials is:
1. Create a new `credentials.json` file with the credentials, from Vertex AI console. (Use a a service account)
2. Store the file in the path specified in `pv.yaml`.
3. Set the `hostPath.path` to the path where the credentials are stored. (The parent directory)

* This parent directory must contain the `credentials.json` file and the `config.yaml` file.
* Set the values of config path in `deployment.yaml` to the path where the config is stored.
* Set the values of credentials path in `config.yaml` to the path where the credentials are stored.

For example:
```yaml
  - model_name: Gemini 3 Pro
    litellm_params:
      model: vertex_ai/gemini-3-pro-preview
      vertex_project: your-project-id
      vertex_location: us-east5
      vertex_credentials: /app/config/vertex/credentials.json
```

### 5. Edit environment variables in the deployment.yaml file

Edit the deployment.yaml file with:
- `DATABASE_URL`: Connection string to the `litellm_db` service.
- `OLLAMA_HOST`: URL of the Ollama service.
- `STORE_MODEL_IN_DB`: Set to "True" to manage models in the database (and also in the UI).

## Deployment

Apply the Persistent Volume, Claim, Deployment, and Service:
```bash
microk8s kubectl apply -f pv.yaml
microk8s kubectl apply -f pvc.yaml
microk8s kubectl apply -f deployment.yaml
microk8s kubectl apply -f service.yaml
```

## Verification
Check if the pods are running:
```bash
microk8s kubectl -n box get pods -l app=litellm
```

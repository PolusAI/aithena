# LiteLLM Database Deployment

This directory contains the deployment for the dedicated PostgreSQL database used by LiteLLM.

## Description
`litellm_db` is a PostgreSQL instance used solely by the `litellm` service for logging, caching, and managing keys/users.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.
- **Secrets**: You need to create the `litellm-db-secret` before deploying.

### 1. Create Secret
Copy the sample secret and fill in your actual values:

```bash
cp secret_sample.yaml secret.yaml
```

### 2. Edit the secret
Edit the secret.yaml file with:
- `username`: The database username (default: llmproxy).
- `password`: The database password.

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
- `hostPath.path`: The path where the database data is stored in the host filesystem.

### 5. Edit environment variables in the deployment.yaml file

Edit the deployment.yaml file with:
- `POSTGRES_DB`: The name of the database (default: litellm).

## Deployment

Apply the Persistent Volume, Claim, Deployment, and Service:

```bash
microk8s kubectl apply -f pv.yaml
microk8s kubectl apply -f pvc.yaml
microk8s kubectl apply -f deployment.yaml
microk8s kubectl apply -f service.yaml
```

## Verification
Ensure the database pod is running:
```bash
microk8s kubectl -n box get pods -l app=litellm-db
```

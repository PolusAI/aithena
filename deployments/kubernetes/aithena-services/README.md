# Aithena Services Deployment

This directory contains the Kubernetes deployment for the core database business logic of AskAithena. It is responsible for executing search operations against the main database (PostgreSQL) using pgvector for similarity searches and metadata queries.

## Description
`aithena-services` is responsible for executing search operations against the main database (PostgreSQL) using pgvector for similarity searches and metadata queries.

## Prerequisites
- **Namespace**: Ensure the `box` namespace exists. Or any other namespace you want. You can use the same namespace as the other services.
- **Secrets**: You need to create the `aithena-services-secret` before deploying.

### 1. Create Secret
Copy the sample secret and fill in your actual values:

```bash
cp secret_sample.yaml secret.yaml
```

### 2. Edit the secret
Edit the secret.yaml file with:
- `postgres_password`: The password for the PostgreSQL database.

This needs to be base64 encoded.
```bash
echo -n "your-secure-password" | base64
```
Don't forget to include `-n` to echo the password without a newline.

### 3. Apply the secret

Apply the secret:
```bash
microk8s kubectl apply -f secret.yaml
```

### 4. Edit environment variables in the deployment.yaml file

Edit the deployment.yaml file with:
- `POSTGRES_HOST`: The host of the PostgreSQL database.
- `POSTGRES_PORT`: The port of the PostgreSQL database.
- `POSTGRES_USER`: The user of the PostgreSQL database.
- `POSTGRES_DB`: The database name of the PostgreSQL database.

## Deployment

Apply the deployment and service manifests:

```bash
microk8s kubectl apply -f deployment.yaml
microk8s kubectl apply -f service.yaml
```

## Verification
Check if the pods are running:
```bash
microk8s kubectl -n box get pods -l app=aithena-services
```


# Quick Start Guide

This guide will help you get Aithena Services up and running quickly. Aithena Services now focuses on providing vector memory functionality and integrates with LiteLLM for a complete AI development environment.

## Deployment Options

You have two primary options for deploying Aithena Services:

1. **Complete Stack with Docker Compose** (recommended for most users)
2. **Standalone Memory Service** (for those who want to configure LiteLLM independently)

## Option 1: Complete Stack with Docker Compose

This option sets up the entire development environment including Ollama, LiteLLM, and Aithena Services.

### Prerequisites

- Docker and Docker Compose installed
- Git installed (to clone the repository)
- Basic understanding of terminal/command line

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/aithena-services.git
cd aithena-services
```

### Step 2: Configure Environment Variables

```bash
# Copy the sample .env file
cp .env.sample .env

# Edit the .env file with your preferred settings
nano .env  # or use any text editor
```

At minimum, you should set:
- `PGVECTOR_PASSWORD` - Password for the PostgreSQL/pgvector database
- `LITELLM_DB_PASSWORD` - Password for the LiteLLM database

If you plan to use cloud models, add your API keys:
- `OPENAI_API_KEY` - For OpenAI models
- `GROQ_API_KEY` - For Groq models
- Azure OpenAI settings if applicable

For local models, make sure to set:
- `OLLAMA_DATA_PATH` - Where Ollama data will be stored (e.g., `/Users/username/.ollama`)

### Step 3: Configure LiteLLM

```bash
# Copy the sample config file
cp config.yaml.sample config.yaml

# Edit if needed (the default configuration works for most cases)
nano config.yaml  # or use any text editor
```

The default configuration includes:
- OpenAI-compatible API (port 4000)
- Several Ollama models
- Pass-through endpoints for managing models and connecting to Aithena Services

### Step 4: Start the Services

```bash
docker compose up -d
```

This command starts:
- Ollama for local model hosting
- PostgreSQL with pgvector for vector operations
- Aithena Services for vector memory functionality
- LiteLLM for model management and API

## Option 2: Standalone Memory Service

Use this option if you want to run Aithena Services as a standalone memory service and configure LiteLLM independently.

### Prerequisites

- PostgreSQL with pgvector extension installed
- Python 3.9+

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/aithena-services.git
cd aithena-services
```

### Step 2: Set Up Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Step 3: Configure Environment Variables

Create a `.env` file with the necessary database configuration:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=aithena
```

### Step 4: Start the Service

```bash
uvicorn src.aithena_services.api.main:app --host 0.0.0.0 --port 8000
```

## Using the Memory API

Whether you deployed the complete stack or standalone service, you can use the Memory API for vector operations:

```python
import requests
import json

# Example: Search for similar vectors
vector = [0.1, 0.2, ...]  # Your embedding vector

response = requests.post(
    "http://localhost:8000/memory/pgvector/search",
    json={
        "table_name": "my_vectors",
        "vector": vector,
        "n": 5
    }
)

similar_items = response.json()
print(json.dumps(similar_items, indent=2))
```

## Using with LiteLLM (Complete Stack Deployment)

If you deployed the complete stack, you can use LiteLLM for model access:

```python
import openai

# Configure the client to use your local LiteLLM server
client = openai.OpenAI(
    api_key="anything",  # The key doesn't matter for local use
    base_url="http://localhost:4000/v1"
)

# Generate embeddings for vector search
response = client.embeddings.create(
    model="nomic-embed-text",  # Or another embedding model
    input="This is a test embedding"
)

embedding_vector = response.data[0].embedding

# Use the vector with Aithena Services memory API
# (See the Memory API example above)
```

## Common Issues and Solutions

- **Database connection errors**: Verify PostgreSQL is running and pgvector extension is installed
- **API keys not working**: Ensure there are no quotes around values in the `.env` file
- **Integration issues**: Check that both services (LiteLLM and Aithena Services) are properly configured

## Next Steps

- Read the [API Reference](api.md) to learn about all available memory endpoints
- Explore [Memory and Vector Database Features](memory.md) for details on vector operations
- Configure environment variables as needed in [Environment Variables](env.md)

## For Production Use

Before using Aithena Services in production:
- Set up authentication
- Use strong passwords for all database services
- Configure CORS settings if needed
- Consider setting up TLS/HTTPS with a reverse proxy 
# Environment Variables for Aithena Services

This document describes the environment variables used to configure Aithena Services.

## Service Configuration

These variables configure the Aithena Services application itself.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AITHENA_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `IVFFLAT_PROBES` | Number of probes for IVFFlat index search | None | No |

## Database Configuration

Aithena Services connects to a PostgreSQL database with the pgvector extension.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` | No |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | No |
| `POSTGRES_USER` | PostgreSQL username | `postgres` | No |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` | No |
| `POSTGRES_DB` | PostgreSQL database name | `postgres` | No |

## Docker Compose Configuration

When using Docker Compose, additional variables are used to configure the container environment and other services like LiteLLM and Ollama.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PGVECTOR_DATA_PATH` | Path to PGVector data directory | `./pgdata` | No |
| `PGVECTOR_PASSWORD` | Password for the PGVector container | `password` | Yes |
| `OLLAMA_DATA_PATH` | Path to Ollama data directory | `./ollama` | No |
| `LITELLM_DB_PASSWORD` | Password for LiteLLM database | `litellmpassword` | Yes |
| `LITELLM_MASTER_KEY` | Master key for LiteLLM API | None | No |

### LLM Provider Keys (for LiteLLM)

If you are using cloud LLM providers via the LiteLLM integration:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY`
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`

## Example .env File

```bash
# Aithena Services DB Config
POSTGRES_HOST=pgvector
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=aithena

# Docker Compose Config
PGVECTOR_PASSWORD=secure_password
LITELLM_DB_PASSWORD=litellm_secure_password

# Optional: LLM Keys
OPENAI_API_KEY=sk-...
```

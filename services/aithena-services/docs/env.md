# Environment Variables for Aithena Services

This document describes the environment variables used to configure Aithena Services with a focus on the memory and vector database functionality, which is now the primary purpose of the service.

## Database Configuration (Primary Focus)

### PostgreSQL / PGVector

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` | No |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | No |
| `POSTGRES_USER` | PostgreSQL username | `postgres` | No |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` | No |
| `POSTGRES_DB` | PostgreSQL database name | `postgres` | No |

## Docker Compose Configuration

When using Docker Compose for the complete stack deployment, additional environment variables are used to configure the integrated services:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OLLAMA_DATA_PATH` | Path to Ollama data directory | `./ollama` | No |
| `PGVECTOR_DATA_PATH` | Path to PGVector data directory | `./pgdata` | No |
| `PGVECTOR_PASSWORD` | PGVector database password | `password` | Yes |
| `PGVECTOR_USER` | PGVector database username | `postgres` | No |
| `PGVECTOR_DB` | PGVector database name | `aithena` | No |
| `LITELLM_DB_USER` | LiteLLM database username | `llmproxy` | No |
| `LITELLM_DB_PASSWORD` | LiteLLM database password | `litellmpassword` | Yes |
| `LITELLM_MASTER_KEY` | Master key for LiteLLM API authentication | None | Recommended for production |


## LLM Provider Configuration (For Complete Stack Only)

These variables are used when deploying the complete stack with Docker Compose and configure the LiteLLM component, not Aithena Services directly:

### OpenAI

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | None | Only if using OpenAI models |

### Azure OpenAI

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | None | Only if using Azure OpenAI |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | None | Only if using Azure OpenAI |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version | None | Only if using Azure OpenAI |


### Anthropic

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key | None | Only if using Claude models |

### Groq

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Groq API key | None | Only if using Groq models |

## Using Environment Variables

You can set environment variables in several ways:

1. In a `.env` file in the project root
2. As environment variables in your shell
3. In Docker Compose through the `.env` file or `environment` section

### Example `.env` File for Standalone Memory Service

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=aithena
```

### Example `.env` File for Complete Stack Deployment

```bash
# Database Configuration
POSTGRES_HOST=pgvector
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=aithena

# Docker Compose Configuration
PGVECTOR_PASSWORD=secure-password
LITELLM_DB_PASSWORD=another-secure-password

# Optional: LLM Provider Configuration
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
OLLAMA_HOST=http://ollama:11434
```

## Important Notes

- Never put quotation marks around values in `.env` files
- API keys should be kept secret and not committed to version control
- For production use, always use strong passwords
- When deploying standalone memory service, focus on the PostgreSQL configuration only 
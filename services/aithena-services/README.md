# Aithena Services

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0--dev0-blue" alt="Version 1.1.3">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT">
</p>

> **Complete AI Stack with Powerful Memory Capabilities**

## 🚀 Building the Complete AI Development Environment

Aithena Services is part of a powerful, integrated AI development stack that brings together local and cloud LLMs, vector memory, and database functionality through a unified API. This complete solution enables you to build sophisticated AI applications with minimal setup and maximum flexibility.

While Aithena Services specializes in robust vector memory and database functionality, it's designed to work as part of a complete ecosystem that includes LiteLLM for model access, Ollama for local LLMs, and vector database capabilities — all through a consistent, OpenAI-compatible API.

### 🧠 The Memory Layer for Your AI Applications

Aithena Services handles the storage and retrieval of information while integrating perfectly with language model providers, letting you build more sophisticated AI solutions with long-term memory capabilities.

**⚡ Looking for quick deployment?** Check out our [Docker Compose Setup](docs/docker_compose.md) to get a complete AI stack running in minutes.

## 🏗️ System Architecture

<p align="center">
  <img src="docs/resources/architecture.svg" alt="Aithena Services Architecture" width="800">
</p>

The diagram above shows how Aithena Services fits into a complete AI stack, providing vector memory capabilities that integrate with LiteLLM for a unified solution. 🧩 Each component plays a vital role in the complete ecosystem.

## ✨ Key Features

- **Vector Database**: Built-in PostgreSQL/pgvector integration for efficient vector storage and similarity search
- **Seamless Integration**: Works perfectly with LiteLLM for a complete AI stack
- **Memory API**: Clean, well-documented API for storing and retrieving vector embeddings
- **Docker Ready**: Deploy as a standalone service or as part of a complete stack
- **Optimized Performance**: Efficient cosine similarity search for finding relevant content
- **CLI Interface**: Simple command-line tool to start and manage the API server
- **Environment Control**: Flexible configuration through environment variables and .env files

## 🤔 Why Choose Aithena Services?

- **Focus on Memory**: Specialized in vector storage and retrieval, doing one thing exceptionally well
- **Cloud-Agnostic**: Works with any LLM provider through LiteLLM integration
- **Simple API**: Clean, consistent interface for all memory operations
- **Production Ready**: Designed for reliability and performance in production environments
- **Active Development**: Constantly improving with new features and optimizations

## 🐳 Recommended Deployment

**We strongly recommend using our Docker Compose stack** for the best experience with Aithena Services. This approach gives you a complete, pre-configured AI development environment with just a few commands.

```bash
# Configure and start
cp .env.sample .env
cp config_sample.yaml config.yaml
# Edit .env and config.yaml with your settings
docker compose up -d
```

For detailed setup instructions, see our [Docker Compose guide](docs/docker_compose.md).

### 🚀 Why Docker Compose is Better

Our Docker Compose stack provides:

- **Unified API Gateway**: Connect to multiple LLM providers (OpenAI, Anthropic, Claude, Groq, etc.) through a single API
- **Integrated Memory Layer**: Seamless vector storage for building apps with long-term memory and context
- **Embedding Generation**: Built-in support for creating and storing embeddings from various providers
- **Local Model Support**: Run open-source models locally with Ollama integration
- **Pre-configured Components**: All services are pre-configured to work together perfectly
- **One-command Deployment**: Get your entire AI stack running with a single command

The complete stack includes:

- **Aithena Services**: Memory/vector functionality
- **LiteLLM**: OpenAI-compatible API for model access
- **Ollama**: Local model hosting
- **PGVector**: Vector database
- **LiteLLM UI**: Web dashboard for monitoring and management

While you can run Aithena Services as a standalone memory component, the full stack delivers a significantly more powerful developer experience.

## 🔍 Quick Usage Examples

### Start the API Server

After installation, you can quickly start the API server using the built-in CLI:

```bash
# Basic usage with default settings (host: 0.0.0.0, port: 8000)
aithena-services serve

# Enable auto-reload for development (automatically reloads on code changes)
aithena-services serve --reload

# Customize host and port
aithena-services serve --host 127.0.0.1 --port 8080

# Set custom log level
aithena-services serve --log-level DEBUG

# Specify a custom .env file location
aithena-services serve --env-file /path/to/your/.env

# View all available options
aithena-services serve --help
```

### Environment Configuration

Aithena Services automatically looks for a `.env` file in your current working directory or parent directories. You can create a `.env` file with settings like:

```
# Database connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
```

If you want to explicitly specify a different `.env` file location, use the `--env-file` flag when starting the server.

### Store Vector Embeddings

```bash
curl -X POST http://localhost:8000/memory/pgvector/insert \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "my_documents",
    "id": "doc1",
    "vector": [0.1, 0.2, 0.3, ...],
    "metadata": {"title": "Important Document", "content": "This contains key information"}
  }'
```

### Search for Similar Content

```bash
curl -X POST http://localhost:8000/memory/pgvector/search \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "my_documents",
    "vector": [0.1, 0.2, 0.3, ...],
    "n": 5
  }'
```

## 📚 Documentation

Comprehensive documentation is available to help you get started:

- [Quick Start Guide](docs/quickstart.md)
- [Docker Compose Setup](docs/docker_compose.md)
- [API Reference](docs/api.md)
- [Memory Features](docs/memory.md)
- [Environment Variables](docs/env.md)
- [Project Structure](docs/structure.md)
- [CLI Usage](docs/cli.md)

## 🔌 Integration with LiteLLM

When deployed with Docker Compose, Aithena Services integrates perfectly with LiteLLM through a convenient passthrough, allowing you to:

1. Access vector memory at `http://localhost:4000/memory/...`
2. Use LLM functionality at `http://localhost:4000/chat/completions`

This means your application only needs to talk to a single API endpoint for both memory and LLM functionality.

## 👥 Community and Support

- **GitHub Issues**: Report bugs or request features
- **Contributions**: Pull requests are welcome
- **Documentation**: Detailed examples and guides available

## 📄 License

Aithena Services is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

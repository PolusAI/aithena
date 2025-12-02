# Aithena Services Documentation

<p align="center">
  <img src="https://img.shields.io/badge/version-1.1.3-blue" alt="Version 1.1.3">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT">
</p>

Welcome to the Aithena Services documentation. Aithena Services is a specialized component that provides vector memory and database functionality for AI applications. It works seamlessly with LiteLLM for a complete AI development environment.

## Deployment Options

Aithena Services offers two primary deployment options:

1. **Complete Stack with Docker Compose**: Deploy the entire AI development stack including Ollama, LiteLLM, and Aithena Services for vector memory.
2. **Memory Component Only**: Use Aithena Services as a standalone memory service.

## Documentation Sections

### Getting Started
- [Quick Start Guide](quickstart.md) - Get up and running with Aithena Services
- [Docker Compose Setup](docker_compose.md) - Detailed instructions for deploying the complete stack

### Core Concepts
- [API Reference](api.md) - Memory API endpoints documentation
- [Memory and Vector Database Features](memory.md) - Using vector databases for storing and retrieving embeddings
- [Filtering Works](filter_works.md) - How to filter search results by language and publication year

### Configuration and Structure
- [Environment Variables](env.md) - Configuring Aithena Services with environment variables
- [Project Structure](structure.md) - Overview of the codebase structure and main components

## Current System Architecture

![Aithena Services Architecture](resources/architecture.svg)

## Project Structure

The current Aithena Services focuses on:

```
src/aithena_services/
├── api/            - FastAPI endpoints for memory operations
├── memory/         - Vector database functionality
│   └── pgvector.py - PostgreSQL vector database implementation
└── cli/            - Command line interface
```

## Key Features

- **Vector Memory**: Retrieve embeddings using PostgreSQL with pgvector
- **Similarity Search**: Efficient cosine similarity search for vectors with metadata
- **Advanced Filtering**: Filter search results by language and publication year
- **Integration with LiteLLM**: Works with LiteLLM for a complete AI development environment
- **Docker-Ready**: Easy deployment with Docker Compose


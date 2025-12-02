# Aithena

**Aithena** is the umbrella repository for all Aithena projects, providing a complete ecosystem for building advanced AI services, specifically focused on scientific research assistance and RAG (Retrieval-Augmented Generation) systems.

This monorepo contains the agents, applications, services, and deployment configurations required to run the full stack.

## 📂 Project Structure

| Directory | Description |
|-----------|-------------|
| **`apps/`** | User-facing applications. Contains the **Ask Aithena Web App**, a modern Next.js interface. |
| **`agents/`** | AI Agents and logic. Contains the **Ask Aithena Agent**, the core RAG intelligence. |
| **`services/`** | Backend microservices. Includes **Aithena Services** for vector memory and LLM integration. |
| **`deployments/`** | Infrastructure as Code. Helm charts, Kubernetes manifests, and Slurm scripts. |
| **`jobs/`** | Data ingestion and processing jobs (e.g., fetching OpenAlex data). |
| **`embeddings/`** | Shared libraries for embedding generation and management. |
| **`mcp/`** | Model Context Protocol implementations. |

## 🚀 Core Components

### 1. [Ask Aithena Agent](agents/ask-aithena-agent/README.md)
The brain of the operation. A sophisticated RAG system that answers scientific questions based on 150+ million academic articles.
- **Key Features**: Multi-agent architecture (Semantic Extractor, Retriever, Responder), 3 protection levels (Owl, Shield, Aegis), and Pydantic AI integration.

### 2. [Ask Aithena App](apps/ask-aithena-app/README.md)
The face of the platform. A Next.js web application that provides a chat interface for users to interact with the agent.
- **Key Features**: Real-time streaming, RabbitMQ updates, and a responsive UI.

### 3. [Aithena Services](services/aithena-services/README.md)
The backbone. A service layer handling vector memory (pgvector), database functionality, and LiteLLM integration.
- **Key Features**: Unified API for LLMs and memory, optimized vector search.

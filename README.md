# Aithena

**Aithena** is the umbrella repository for all Aithena projects, providing a complete ecosystem for building advanced AI services, specifically focused on scientific research assistance and RAG (Retrieval-Augmented Generation) systems.

This monorepo contains the agents, applications, services, and deployment configurations required to run the full stack.

## 🏗️ Architecture & Documentation

We have detailed architectural documentation available in the `diagrams/` directory.

*   **[AskAithena Structure](diagrams/AskAithena_Structure.md)**: A detailed guide to the AskAithena platform architecture, detailing services, their roles, and interactions.
*   **[System Architecture](diagrams/aithena-architecture.md)**: A high-level overview of the entire Aithena ecosystem on the Polus servers.

> **Note**: For visual diagrams, see the `.svg` files in the `diagrams/` directory (e.g., `AskAithena_Structure.svg`).

## 📂 Project Structure

| Directory | Description |
|-----------|-------------|
| **`agents/`** | AI Agents and logic. Contains the **Ask Aithena Agent**, the core RAG intelligence. |
| **`apps/`** | User-facing applications. Contains the **Ask Aithena Web App**, a modern Next.js interface. |
| **`deployments/`** | Infrastructure as Code. Helm charts, Kubernetes manifests, and Slurm scripts. |
| **`embeddings/`** | Shared libraries for embedding generation and management. |
| **`jobs/`** | Data ingestion and processing jobs (e.g., fetching OpenAlex data). |
| **`mcp/`** | Model Context Protocol implementations (e.g., **Ask Aithena MCP**). |
| **`services/`** | Backend microservices. Includes **Aithena Services** for vector memory and LLM integration. |
| **`templates/`** | Project templates for creating new services or agents. |

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

## 🛠️ Deployment

All deployment configurations are located in the `deployments/` directory.

### Kubernetes (`deployments/kubernetes/`)

The `deployments/kubernetes/` directory contains manifests for deploying individual services.

> **IMPORTANT**: Each subdirectory in `deployments/kubernetes/` (e.g., `postgres`, `litellm`, `ask-aithena-app`) contains its own `README.md` with specific deployment instructions, configuration details, and prerequisites. **Please consult these individual READMEs before deploying.**

*   **[Postgres](deployments/kubernetes/postgres/README.md)**: Database configuration and initialization.
*   **[LiteLLM](deployments/kubernetes/litellm/README.md)**: LLM Gateway deployment.
*   **[Ask Aithena App](deployments/kubernetes/ask-aithena-app/README.md)**: Frontend deployment.
*   ...and others.

### Helm (`deployments/helm/`)
Helm charts for packaging and deploying the applications.

### Slurm (`deployments/slurm/`)
Scripts for running jobs in HPC environments (Singularity/Apptainer).

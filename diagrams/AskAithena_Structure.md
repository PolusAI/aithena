# AskAithena Architecture Guide

This document outlines the architecture of the AskAithena platform, detailing the services, their roles, and how they interact to provide intelligent query capabilities.

## Overview

AskAithena is a microservices-based application that leverages Large Language Models (LLMs) and vector search to provide answers based on scientific data. The architecture is designed to be modular, separating the user interface, agent logic, model inference, and data storage.

## Components & Services

### User Interface
- **ask-aithena-app**: The web-based UI for the application. It provides the interface for users to submit queries and view real-time responses.

### Application Logic
- **ask-aithena-agent**: The central brain of the system. It hosts the agents that orchestrate the workflow: processing user queries, requesting embeddings, performing vector searches, and generating responses.
- **rabbitmq**: A message broker used for real-time communication. It allows the `ask-aithena-agent` to stream status updates and partial responses back to the `ask-aithena-app` asynchronously.

### AI & Inference Gateway
- **litellm**: A unified API gateway for LLM interactions. It abstracts the differences between various LLM providers.
    - **Role**: It acts as the single entry point for the agent to access both text generation (LLMs) and specific backend tools.
    - **Passthrough**: Uniquely, it also routes specific requests to `aithena-services`, effectively acting as a proxy for search capabilities.
- **litellm_db**: A dedicated PostgreSQL database used solely by `litellm` for logging, caching, or managing keys/users.

### Core Backend Services
- **aithena-services**: Contains the core business logic for data retrieval.
    - **Function**: It executes search operations against the main database, including pgvector similarity searches and direct metadata queries (e.g., by DOI).
- **arctic**: A dedicated vLLM-based gRPC server specifically for generating vector embeddings from text. This is high-performance and optimized for the embedding model.
- **ollama**: A local inference service for running LLMs (like Llama 3, Mistral, etc.) within the cluster, avoiding external API dependencies for certain tasks.

### Data Storage
- **postgres**: The primary data store for AskAithena.
    - **Features**: It is enabled with `pgvector` to store and query high-dimensional vector embeddings of the scientific literature or data being queried.

## Data Flow & Connectivity

The services communicate in a hierarchical manner to fulfill a user request:

1.  **User Request**: The user submits a query via **ask-aithena-app**.
2.  **Processing**: The app sends the request to **ask-aithena-agent**.
3.  **Updates**: Throughout the process, the agent publishes real-time progress to **rabbitmq**, which the app consumes to update the UI.
4.  **Embedding**: The agent sends text to **arctic** to generate vector embeddings.
5.  **Search & Retrieval**:
    *   The agent sends a search request to **litellm**.
    *   **litellm** identifies this as a tool call and passes the request to **aithena-services**.
    *   **aithena-services** queries **postgres** (using vector similarity or SQL) and returns relevant chunks/documents.
6.  **Generation**:
    *   The agent constructs a prompt with the retrieved context.
    *   The agent sends the prompt to **litellm** for completion.
    *   **litellm** routes this to the configured model provider, which could be **ollama** (local) or an external provider.

## Diagram

Please refer to `AskAithena_Structure.svg` for a visual representation of these relationships.


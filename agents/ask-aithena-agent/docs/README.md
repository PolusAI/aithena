# Ask Aithena Agent Documentation

This directory contains technical documentation, architecture diagrams, and visual references for the **Ask Aithena Agent** system.

## Documentation Index

### 1. Technical Reference
- **File:** [`technical_reference.md`](technical_reference.md)
- **Description:** The primary technical guide for the system. It details:
    - **System Overview:** High-level RAG architecture.
    - **Agent Inventory:** Deep dive into Semantic Extractor, Context Retriever, and Responder agents.
    - **Protection Levels:** Detailed logic for Owl, Shield, and Aegis workflows (Pass-through vs. Batch vs. Iterative).
    - **Feedback Loops:** Explanations of the self-correction mechanisms in Semantic Extraction and Shield Reranking.
    - **Infrastructure:** Integration with RabbitMQ and PGVector.

### 2. Architecture Diagrams
- **File:** [`architecture_diagram.svg`](architecture_diagram.svg)
    - **Description:** A high-fidelity scalable vector graphic visualizing the entire pipeline. It clearly shows the parallel processing lanes for the three protection levels (Owl, Shield, Aegis) and the internal loops within the agents.
- **File:** [`architecture_diagram.md`](architecture_diagram.md)
    - **Description:** The source code for the architecture diagram in **Mermaid** format. Useful for version control or rendering in Markdown-compatible viewers (like GitHub).

### 3. Visual Workflows (Supplementary)
These images provide additional visual context for specific parts of the system workflow:

- **File:** `general_architecture.jpeg`
    - **Description:** High-level overview of the entire Aithena platform architecture.
- **File:** `agents_workflow_1.jpeg`
    - **Description:** Detailed flow of the initial request processing and semantic extraction phases.
- **File:** `agents_workflow_2.jpeg`
    - **Description:** detailed flow of the reranking and response generation phases, focusing on the interaction between the Reranker and Responder agents.

---

## Quick Links
- [Back to Agent Source Code](../src/)
- [Back to Agent README](../README.md)


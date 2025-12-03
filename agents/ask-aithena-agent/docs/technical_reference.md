# Technical Reference: Ask Aithena Agent

**Version:** 1.2.0  
**Date:** 2024

## 1. System Overview

Ask Aithena is a Retrieval-Augmented Generation (RAG) system designed to answer scientific questions using a database of over 150 million academic articles. The core differentiator of Ask Aithena is its **Protection Levels** system, which allows users to trade off latency for accuracy through progressively more complex reranking pipelines.

The system is built on a multi-agent architecture using **Pydantic AI**, enabling type-safe interaction with LLMs, structured output validation, and **self-correcting feedback loops**.

---

## 2. Architecture Components & Feedback Loops

### 2.1. Semantic Extractor Agent (Iterative Refinement)
- **Source:** `agents/semantic_extractor.py`
- **Model:** `mistral-small3.2` (Default)
- **Role:** Pre-processing user queries to optimize them for vector embedding.
- **Why it matters:** Users often ask conversational questions ("What is...?", "Tell me about..."). Embedding these raw queries adds noise. This agent extracts the core semantic subject.
- **The Feedback Loop:**
    1.  **Proposal:** The main agent receives the raw query and calls the `extract_semantics` tool (powered by an "Expert" LLM) to propose a search sentence.
    2.  **Critique:** The main agent evaluates the proposal against strict criteria (must not answer the question, must expand acronyms, must not lose info).
    3.  **Refinement:** If the proposal is flawed, the main agent calls `extract_semantics` *again* with specific `extra_instructions` to fix the error. This loop continues until the agent is satisfied.
    4.  **Output:** A single, optimized string for embedding.

### 2.2. Context Retriever
- **Source:** `agents/context_retriever.py`
- **Role:** Orchestrator for the retrieval phase.
- **Workflow:**
    1.  Calls **Semantic Extractor** to get the optimized query.
    2.  Publishes status update (`searching_for_works`) to RabbitMQ.
    3.  **Vector Search:**
        -   Embeds the optimized query using the **Arctic** embedding service.
        -   Performs a cosine similarity search against the **PGVector** database (`openalex.abstract_embeddings_arctic`).
        -   Filters by year range and language.
    4.  **Output:** A `Context` object containing a list of `Document` objects (raw search results).

### 2.3. Responder Agent
- **Source:** `agents/responder.py`
- **Model:** `gpt-4.1` (Default)
- **Role:** The final synthesizer that generates the answer.
- **Input:** XML-structured prompt containing the user `<question>` and the retrieved `<context>` (list of docs).
- **Constraints:**
    -   MUST start with a summary paragraph citing multiple sources.
    -   MUST use numbered citations `(1)` corresponding to document indices.
    -   MUST NOT hallucinate or provide medical/legal advice without disclaimers.
    -   Prioritizes lower-index documents (assumed more relevant).

---

## 3. Protection Levels & Reranking Workflows

The system operates in three modes, distinguished by their processing depth and batching strategy.

### 3.1. Level 1: Owl (Fast Mode)
- **Endpoint:** `/owl/ask`
- **Processing Strategy:** **Pass-Through**
- **Workflow:**
    1.  **Retrieve:** `Context Retriever` fetches top N documents (default 10).
    2.  **Pass:** No reranking is performed. The raw similarity order from PGVector is preserved.
    3.  **Respond:** `Context` is passed directly to `Responder Agent`.
- **Use Case:** Low-latency requirements, simple fact retrieval where vector similarity is sufficient.

### 3.2. Level 2: Shield (One-Step Reranker with Self-Correction)
- **Endpoint:** `/shield/ask`
- **Source:** `agents/reranker/one_step_reranker.py`
- **Model:** `o4-mini`
- **Processing Strategy:** **Batch Processing (All-in-One)**
- **Concept:** The entire list of retrieved documents is fed into the LLM's context window at once. The agent sees the "big picture" and reorders the list holistically.
- **The Verification Loop:**
    1.  **Analyze Topic:** Agent calls `define_broad_topic` to understand the domain.
    2.  **Summarize:** Agent calls `describe_works` to get concise summaries of *all* documents.
    3.  **Prompt Gen:** Agent calls `create_reranker_prompt`.
    4.  **Score (Attempt 1):** Agent calls `call_reranker` to assign relevance scores.
    5.  **Verify:** Agent calls `verify_result_list` to check constraints:
        -   *Constraint:* Are all indices unique?
        -   *Constraint:* Is the count correct?
        -   *Constraint:* Are scores sorted descending?
    6.  **Correction:** If `verify_result_list` returns `False`, the agent interprets the error and calls `call_reranker` **again** with corrected instructions.
- **Output:** Reranked `Context`.

### 3.3. Level 3: Aegis (Referee System with Multi-Tool Scrutiny)
- **Endpoint:** `/aegis/ask`
- **Source:** `agents/reranker/aegis/`
- **Models:**
    -   Orchestrator: `o4-mini`
    -   Referee: `o3`
- **Processing Strategy:** **Iterative Individual Processing (One-by-One)**
- **Concept:** Documents are *not* compared to each other directly. Instead, each document is individually "put on trial" by a Referee agent to determine its absolute merit.
- **Workflow:**
    1.  **Orchestrator Loop:** The `aegis_reranker_agent` iterates through every document index `i` in the context.
    2.  **Delegation:** For document `i`, it calls `score_work(i)`.
    3.  **Referee Investigation:** The `referee_agent` starts an investigation for that single document:
        -   *NLP Tool:* Calls `robust_noun_phrase_overlap` (spaCy) for granular lemma overlap.
        -   *NLP Tool:* Calls `simplified_ngram_overlap` (sklearn) for statistical similarity.
        -   *LLM Tool:* Calls `topical_intersection` to check if the subject matter aligns.
        -   *LLM Tool:* Calls `intent_matching` to check if it answers the "why" of the query.
    4.  **Synthesis:** The Referee combines these 4 independent signals into a final score (0-1) and a textual reason.
    5.  **Aggregation:** The Orchestrator collects the result, publishes a status update ("Analyzed doc 5..."), and moves to the next document.
    6.  **Final Sort:** Once all documents are scored, the Orchestrator sorts the list.

---

## 4. Infrastructure Integration

### 4.1. RabbitMQ
- **Exchange:** `ask-aithena-exchange` (Topic)
- **Routing Key:** `session.{session_id}`
- **Purpose:** Provides real-time feedback to the user interface, especially critical for the slow **Aegis** mode.
- **Message Format:**
  ```json
  {
    "timestamp": "ISO-8601",
    "status": "reranking_context",
    "message": "I am currently analyzing document 5 of 10..."
  }
  ```

### 4.2. Vector Search
- **Database:** PostgreSQL with `pgvector` extension.
- **Table:** `openalex.abstract_embeddings_arctic`.
- **Embedding Model:** Snowflake Arctic (served via separate service).

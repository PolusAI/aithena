# Ask Aithena Agent (v1.1.4)

> 🦉 **An advanced AI-powered research assistant agent for answering scientific questions based on 150+ million academic articles.**

This agent is the core intelligence behind the Ask Aithena platform, a RAG (Retrieval-Augmented Generation) system designed to provide evidence-based answers to scientific research questions. It's built with multiple "protection levels" for different accuracy/speed tradeoffs.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
  - [Agents](#agents)
  - [Reranking Systems](#reranking-systems)
  - [Tools](#tools)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Installation & Setup](#installation--setup)
- [Docker Deployment](#docker-deployment)
- [Project Structure](#project-structure)
- [Development Notes](#development-notes)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Ask Aithena Agent Flow                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User Query                                                                │
│       │                                                                     │
│       ▼                                                                     │
│   ┌──────────────────────┐                                                  │
│   │  Semantic Extractor  │  ← Transforms user query into embedding-optimized│
│   │      Agent           │    sentence (removes "what is", expands acronyms)│
│   └──────────┬───────────┘                                                  │
│              │                                                              │
│              ▼                                                              │
│   ┌──────────────────────┐                                                  │
│   │  Context Retriever   │  ← Embeds sentence with Arctic model,            │
│   │                      │    searches PGVector for similar works           │
│   └──────────┬───────────┘                                                  │
│              │                                                              │
│              ▼                                                              │
│   ┌──────────────────────────────────────────────────────────────┐          │
│   │                    Reranker (Optional)                       │          │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │          │
│   │  │    NONE     │  │   SHIELD    │  │       AEGIS         │   │          │
│   │  │  (Owl Mode) │  │(One for All)│  │(Individual Analysis)│   │          │
│   │  └─────────────┘  └─────────────┘  └─────────────────────┘   │          │
│   └──────────┬───────────────────────────────────────────────────┘          │
│              │                                                              │
│              ▼                                                              │
│   ┌──────────────────────┐                                                  │
│   │   Responder Agent    │  ← Generates final answer with citations         │
│   │                      │    from reranked/ordered documents               │
│   └──────────────────────┘                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Protection Levels

The system offers three "protection levels" that trade off between speed and accuracy:

| Level    | Reranking       | Speed   | Accuracy | Use Case                        |
|----------|-----------------|---------|----------|----------------------------------|
| **Owl**  | None            | Fast    | Good     | Quick lookups, simple questions  |
| **Shield** | One-Step      | Medium  | Better   | Standard research questions      |
| **Aegis** | Referee-Orchestrator | Slow | Best   | Critical research, complex queries |

---

## Core Components

### Agents

All agents are built using **[Pydantic AI](https://docs.pydantic.dev/latest/concepts/pydantic_ai/)** and communicate with LLMs via **LiteLLM**.

#### 1. Semantic Extractor Agent (`agents/semantic_extractor.py`)

**Purpose:** Transforms user questions into embedding-optimized sentences.

**Why it exists:** Raw user queries often contain unnecessary words like "What is..." or "How do I..." that dilute embedding quality. This agent extracts the core semantic content while preserving ALL important information.

**Example:**
```
Input:  "What is the recommended treatment for colon cancer in prediabetic teenagers?"
Output: "recommended treatment for colon cancer in prediabetic teenagers"
```

**Key Rules:**
- MUST preserve all information from original query
- Expands acronyms if confident (AI → Artificial Intelligence)
- NEVER adds information not in original query
- NEVER attempts to answer the question

**Architecture:**
- `semantic_agent` (main) - Orchestrates the extraction
- `semantic_extractor_agent` (tool) - Expert LLM that proposes candidate sentences
- Uses `extract_semantics` tool for iterative refinement

**Models Used:** `SEMANTICS_MODEL` (default: `mistral-small3.2`)

---

#### 2. Context Retriever (`agents/context_retriever.py`)

**Purpose:** Orchestrates semantic extraction + vector search to retrieve relevant documents.

**Flow:**
1. Calls `run_semantic_agent()` to get optimized query
2. Publishes status to RabbitMQ (if broker connected)
3. Calls `get_similar_works_async()` to fetch documents from PGVector
4. Constructs `Context` object with retrieved documents

**Key Parameters:**
- `similarity_n`: Number of documents to retrieve
- `languages`: Filter by document language (default: `["en"]`)
- `start_year`, `end_year`: Filter by publication year

---

#### 3. Responder Agent (`agents/responder.py`)

**Purpose:** Generates the final answer with proper citations based on retrieved documents.

**Prompt Rules (from `prompts/responder.txt`):**
- MUST start with a summary paragraph citing ALL documents
- Uses numbered citations like `(1)`, `(2)` matching document indices
- Cannot give legal/medical advice (includes disclaimers)
- Prioritizes lower-indexed documents (they're more relevant)
- NEVER makes up information
- Uses markdown formatting

**Input Format:**
```xml
<question>User's question here</question>
<context>
  <doc>
    <index>1</index>
    <content>Abstract text...</content>
    <reason>Optional: why this doc is relevant</reason>
  </doc>
  ...
</context>
```

**Models Used:** `RESPONDER_MODEL` (configurable, default: `gpt-4.1`)

---

#### 4. Talker Agent (`agents/talker.py`)

**Purpose:** Handles follow-up conversation after initial response.

**Note:** Currently defined but the endpoint is commented out in the API. Intended for conversational follow-ups using the same context.

**Models Used:** `TALKER_MODEL` (configurable)

---

### Reranking Systems

#### One-Step Reranker (Shield Level) - `agents/reranker/one_step_reranker.py`

**Purpose:** Quick single-pass reranking using an LLM to score relevance.

**How it works:**
1. `define_broad_topic` tool extracts main topic from query
2. `describe_works` tool summarizes the retrieved documents
3. `create_reranker_prompt` tool generates a custom reranking prompt
4. `call_reranker` tool scores each document (0-1)
5. `verify_result_list` tool validates the output

**Output:** Updates `Context.reranked_indices` and `Context.reranked_scores`

**Models Used:** `SHIELD_MODEL` (default: `o4-mini`)

---

#### AEGIS Reranker (Aegis Level) - `agents/reranker/aegis/`

**Purpose:** Most thorough reranking using a multi-agent referee system.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    AEGIS Reranker                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────────────────┐                              │
│   │  Orchestrator Agent      │  ← Manages the process       │
│   │  (aegis_reranker_agent)  │    Calls score_work for each │
│   └──────────┬───────────────┘    document                  │
│              │                                              │
│              ▼                                              │
│   ┌──────────────────────────┐                              │
│   │  Referee Agent           │  ← Scores individual docs    │
│   │  (referee_agent)         │                              │
│   │                          │                              │
│   │  Tools available:        │                              │
│   │  - topical_intersection  │  ← Binary: on-topic or not   │
│   │  - intent_matching       │  ← How well intent matches   │
│   │  - robust_noun_phrase_overlap │  ← NLP overlap score    │
│   │  - simplified_ngram_overlap   │  ← N-gram similarity    │
│   └──────────────────────────┘                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Referee Agent Tools (`aegis/tools.py`):**

| Tool | Type | Description |
|------|------|-------------|
| `robust_noun_phrase_overlap` | NLP | Uses spaCy to extract noun phrases and calculate lemma overlap |
| `simplified_ngram_overlap` | NLP | Uses sklearn's CountVectorizer with cosine similarity on 1-3 grams |
| `topical_intersection` | LLM | Binary assessment: is document on-topic? (0 or 1) |
| `intent_matching` | LLM | Scores 0-1 how well document matches query intent |

**Key Feature:** `publish_status` tool keeps users informed during the (slow) reranking process via RabbitMQ.

**Models Used:**
- `AEGIS_ORCHESTRATOR_MODEL` (default: `o4-mini`)
- `AEGIS_REFEREE_MODEL` (default: `o3`)

**Output:** Updates `Context.reranked_indices`, `Context.reranked_scores`, AND `Context.reranked_reasons`

---

### Tools

#### Vector Search (`tools/vector_search.py`)

**Purpose:** Embeds text and searches for similar documents in PGVector.

**Key Functions:**

```python
async def _embed_text(text: str) -> list[float]:
    """Uses Arctic embedding model via ArcticClient"""
    
async def get_similar_works_async(
    text: str,
    similarity_n: int,
    languages: list[str] | None,
    broker: Optional[RabbitBroker],
    session_id: Optional[str],
    start_year: Optional[int],
    end_year: Optional[int],
) -> list[dict]:
    """Fetches similar works from aithena-services PGVector endpoint"""
```

**External Dependencies:**
- `aithena-embeddings` package (Arctic embedding client)
- `aithena-services` API (`/memory/pgvector/search_works`)

---

## API Reference

### Base URL: `http://localhost:8000`

All endpoints that involve reranking require `X-Session-ID` header for RabbitMQ status updates.

### Streaming Endpoints (Real-time Response)

| Endpoint | Level | Description |
|----------|-------|-------------|
| `POST /owl/ask` | Owl | Fast response, no reranking |
| `POST /shield/ask` | Shield | One-step reranking |
| `POST /aegis/ask` | Aegis | Full referee reranking |

**Request Body:**
```json
{
  "query": "What is the treatment for colon cancer?",
  "similarity_n": 10,
  "languages": ["en"],
  "start_year": 2020,
  "end_year": 2024
}
```

**Response:** Server-Sent Events (SSE) stream with:
1. Text chunks (the answer)
2. Final `\n\n\n` delimiter
3. JSON array of references

---

### Non-Streaming Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /answer-owl` | Returns full Owl-level answer |
| `POST /answer-shield` | Returns full Shield-level answer |
| `POST /answer-aegis` | Returns full Aegis-level answer |
| `POST /prompt-owl` | Returns the full prompt that would be sent to LLM |
| `POST /prompt-shield` | Returns Shield-level prompt |
| `POST /prompt-aegis` | Returns Aegis-level prompt |

---

### Utility Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /health` | Detailed health check (tests LiteLLM connection) |
| `POST /get-articles` | Returns similar articles without generating answer |
| `POST /get-article-by-doi` | Fetch specific article by DOI |
| `POST /get-semantic-query` | Returns the semantic extraction of a query |

---

## Configuration

All configuration is done via environment variables. See `.env-sample` for full list.

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_URL` | `http://localhost:4000/v1` | LiteLLM proxy URL |
| `LITELLM_API_KEY` | `sk-1212` | API key for LiteLLM |
| `PROMPTS_DIR` | `./prompts` | Directory containing prompt templates |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | RabbitMQ connection URL |

### Model Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RESPONDER_MODEL` | `gpt-4.1` | Model for generating answers |
| `RESPONDER_MODEL_TEMPERATURE` | `0.3` | Temperature for responder |
| `TALKER_MODEL` | `gpt-4.1` | Model for follow-up chat |
| `SEMANTICS_MODEL` | `mistral-small3.2` | Model for semantic extraction |
| `SEMANTICS_TEMPERATURE` | `0.2` | Temperature for semantics |
| `SHIELD_MODEL` | `o4-mini` | Model for Shield reranker |
| `AEGIS_ORCHESTRATOR_MODEL` | `o4-mini` | Model for Aegis orchestrator |
| `AEGIS_REFEREE_MODEL` | `o3` | Model for Aegis referee |

### Embedding Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ARCTIC_HOST` | `localhost` | Host for Arctic embedding service |
| `ARCTIC_PORT` | `8000` | Port for Arctic embedding service |
| `EMBEDDING_TABLE` | `openalex.abstract_embeddings_arctic` | PGVector table for embeddings |
| `SIMILARITY_N` | `10` | Default number of documents to retrieve |

### Optional Model Parameters

All models support additional parameters (all optional):
- `*_MODEL_FREQUENCY_PENALTY`
- `*_MODEL_MAX_TOKENS`
- `*_MODEL_TOP_P`
- `*_MODEL_PRESENCE_PENALTY`
- `*_MODEL_SEED`

### Logging & Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_LOGFIRE` | `false` | Enable Pydantic Logfire tracing |
| `LOGFIRE_TOKEN` | - | Logfire API token |
| `AITHENA_LOG_LEVEL` | `INFO` | Python logging level |

---

## Installation & Setup

### Prerequisites

- Python 3.12 (exactly - not 3.13+)
- [uv](https://docs.astral.sh/uv/) package manager
- Running instances of:
  - LiteLLM proxy
  - RabbitMQ
  - PostgreSQL with PGVector + embedded documents
  - Arctic embedding service

### Local Development

```bash
# Clone and navigate
cd agents/ask-aithena-agent

# Install dependencies with uv
uv sync

# Copy and configure environment
cp .env-sample .env
# Edit .env with your configuration

# Run the server
uv run ask-aithena serve --host 0.0.0.0 --port 8000 --log-level DEBUG

# Or with reload for development
uv run ask-aithena serve --reload
```

### CLI Commands

```bash
# Show version
uv run ask-aithena --version

# Start server
uv run ask-aithena serve [OPTIONS]

# Options:
#   --host TEXT       Host to bind to (default: 0.0.0.0)
#   --port INTEGER    Port to bind to (default: 8000)
#   --reload          Enable auto-reload on code changes
#   --log-level TEXT  Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
```

---

## Docker Deployment

### Build Image

```bash
# From repository root
./agents/ask-aithena-agent/build-docker.sh
```

**What the build script does:**
1. Creates staging directory at `${repo_root}/docker_build/`
2. Copies necessary files (common, embeddings, agent code)
3. Builds image tagged as `polusai/ask-aithena-agent:${version}[-${arch}]`
4. Cleans up staging directory

**Note:** The Dockerfile expects the `embeddings` directory at a specific path (`../../embeddings`). The build script handles this.

### Run Container

```bash
docker run -p 8000:8000 \
  -e LITELLM_URL=http://litellm:4000/v1 \
  -e LITELLM_API_KEY=your-key \
  -e RABBITMQ_URL=amqp://rabbitmq:5672/ \
  polusai/ask-aithena-agent:1.1.4
```

### Environment Variables for Docker

All configuration from the [Configuration](#configuration) section applies. The container runs as non-root user `user` (uid 1000).

---

## Project Structure

```
ask-aithena-agent/
├── src/polus/aithena/ask_aithena/
│   ├── __init__.py              # Package version
│   ├── config.py                # All configuration/env vars
│   ├── models.py                # Pydantic models (Document, Context)
│   ├── rabbit.py                # RabbitMQ exchange/queue definitions
│   ├── logfire_logger.py        # Conditional Logfire wrapper
│   ├── ask_aithena.py           # Legacy API (deprecated, kept for reference)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── context_retriever.py # Orchestrates semantic + vector search
│   │   ├── semantic_extractor.py # Extracts embedding-ready sentences
│   │   ├── responder.py         # Generates final answers
│   │   ├── talker.py            # Follow-up conversation agent
│   │   │
│   │   └── reranker/
│   │       ├── __init__.py
│   │       ├── one_step_reranker.py  # Shield-level reranker
│   │       │
│   │       └── aegis/
│   │           ├── __init__.py
│   │           ├── referee_orchestrator.py  # Aegis orchestrator
│   │           ├── single_agent.py          # Referee scoring agent
│   │           └── tools.py                 # NLP tools (spaCy, sklearn)
│   │
│   ├── api/
│   │   ├── __init__.py          # Legacy FastAPI app
│   │   └── app.py               # Main FastAPI application
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py              # CLI entry point
│   │
│   └── tools/
│       ├── __init__.py
│       └── vector_search.py     # Embedding + PGVector search
│
├── prompts/
│   ├── responder.txt            # Responder agent system prompt
│   │
│   ├── semantics/
│   │   └── main_agent.txt       # Semantic extraction prompt
│   │
│   └── reranker/
│       ├── one_step_agent.txt   # Shield reranker prompt
│       ├── create_prompt.txt    # Prompt generator for reranker
│       ├── describe_works.txt   # Works description generator
│       ├── define_topic.txt     # Topic extraction prompt
│       │
│       └── referee/
│           ├── orchestrator.txt # Aegis orchestrator prompt
│           └── single_agent.txt # Referee scoring prompt
│
├── pyproject.toml               # Project dependencies & config
├── uv.lock                      # Locked dependencies
├── VERSION                      # Current version (1.1.4)
├── .bumpversion.cfg             # Version bumping configuration
├── .env-sample                  # Environment template
├── Dockerfile                   # Container build instructions
├── build-docker.sh              # Docker build script
└── .dockerignore                # Docker ignore patterns
```

---

## Development Notes

### Adding a New Agent

1. Create new file in `src/polus/aithena/ask_aithena/agents/`
2. Define your agent using Pydantic AI:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from polus.aithena.ask_aithena.config import LITELLM_URL, LITELLM_API_KEY

model = OpenAIModel(
    model_name="your-model",
    provider=OpenAIProvider(
        api_key=LITELLM_API_KEY,
        base_url=LITELLM_URL,
    ),
)

your_agent = Agent(
    model=model,
    system_prompt="Your prompt here",
    output_type=YourOutputModel,
)
```

3. Add prompt to `prompts/` directory
4. Export from `agents/__init__.py`

### Modifying Prompts

All prompts are in the `prompts/` directory as `.txt` files. Changes take effect on server restart (no rebuild needed if mounting volume).

### RabbitMQ Status Messages

The system publishes status updates during processing:

```python
class ProcessingStatus(BaseModel):
    timestamp: str  # ISO format
    status: str     # e.g., "analyzing_query", "searching_for_works", "reranking_context"
    message: Optional[str]  # Human-readable status
```

Routing: `session.{session_id}` on `ask-aithena-exchange` (TOPIC exchange)

### Testing with Logfire

Enable Logfire for detailed tracing:

```bash
export USE_LOGFIRE=true
export LOGFIRE_TOKEN=your-token
```

This instruments:
- All OpenAI/LiteLLM calls
- FastAPI requests
- HTTPX requests

---

## Next Steps
- Revise conversational flow: currently, each new message in the conversation is handled as a new query (it triggers a new vector search)
- Add the ability for rerankers to completely remove documents from the context if they are not relevant (currently, we trust they will assign a very low score to them and that the responder will not use them in the answer)
- Add a mode where a 'researcher' agent creates a set of queries, executes them, and then with multiple queries/results, it gives a complete answer
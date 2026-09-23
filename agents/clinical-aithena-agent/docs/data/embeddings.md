# Embeddings

GARDIAN uses MedCPT embeddings to enable semantic search — finding clinical trials that are conceptually related to a patient's conditions even when the exact terminology differs. This page explains what MedCPT is, how it's used, and why it was chosen.

## What is MedCPT?

[MedCPT](https://github.com/ncbi-nlp/MedCPT) (Medical Contrastive Pre-Training for Text) is a biomedical text encoder developed by NCBI. It was trained on a large corpus of PubMed articles and their associated search queries, learning to produce vector representations that capture the semantic meaning of biomedical text.

Unlike general-purpose text encoders, MedCPT understands biomedical concepts and their relationships. It knows that "chronic lymphocytic leukemia" and "CLL" refer to the same condition, that "immunotherapy" is related to "checkpoint inhibitor," and that "renal impairment" and "kidney disease" describe overlapping clinical concepts.

## Two-Encoder Architecture

MedCPT uses a **two-encoder architecture**, with separate models for documents and queries:

- **Article encoder** (MedCPT-Article) — Encodes trial information (title + text) into 768-dimensional vectors. Used during indexing to create searchable embeddings for each trial.

- **Query encoder** (MedCPT-Query) — Encodes patient search conditions into 768-dimensional vectors. Used at query time when searching for matching trials.

The two encoders were trained together so that queries and relevant documents end up close together in the embedding space. This means a patient condition like "alpha-galactosidase A deficiency" will be near trials about Fabry disease enzyme replacement therapy — even though the texts share few exact words.

## How Embeddings Are Used

### At Index Time

When a new trial is ingested or updated, its title and full text are each encoded separately using the article encoder. The resulting vectors are stored in PostgreSQL using the pgvector extension, with HNSW (Hierarchical Navigable Small World) indexes for fast approximate nearest-neighbor search.

### At Query Time

When a patient matching request comes in, the extracted search conditions are encoded using the query encoder. These query vectors are compared against the stored trial vectors using cosine similarity, returning the most semantically similar trials.

### In the Hybrid Pipeline

Semantic search results are combined with BM25 keyword search results through Reciprocal Rank Fusion. The semantic component is particularly valuable for:

- **Synonym matching** — Finding trials that use different terms for the same condition
- **Conceptual matching** — Discovering trials in related therapeutic areas
- **Abbreviation handling** — Connecting abbreviations (e.g., "ALS") with full names ("amyotrophic lateral sclerosis")
- **Cross-lingual medical concepts** — Matching conditions described with different medical nomenclatures

## Why MedCPT?

Several factors led to choosing MedCPT over alternatives:

- **Biomedical specialization** — General-purpose encoders (e.g., OpenAI's text-embedding models) are trained on broad web text. MedCPT is trained specifically on biomedical literature, giving it stronger performance on medical concepts.
- **NCBI provenance** — MedCPT was developed by the same organization (NCBI) that created TrialGPT, making it a natural fit for the pipeline.
- **Two-encoder design** — The separate query and article encoders are specifically designed for the retrieval use case, where query text (short conditions) differs structurally from document text (long trial descriptions).
- **Open source** — MedCPT is freely available, allowing self-hosted deployment without API dependencies or per-query costs.

## Model Serving

MedCPT models are served through an OpenAI-compatible API via the LiteLLM proxy, which is part of the shared Aithena platform infrastructure. This provides a consistent interface for embedding generation and allows the models to be served on GPU hardware for optimal throughput.

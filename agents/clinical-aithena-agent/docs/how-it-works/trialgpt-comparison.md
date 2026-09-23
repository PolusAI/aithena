# TrialGPT Foundation and Comparative Analysis

GARDIAN's patient matching workflow is based on [TrialGPT](https://github.com/NCBI-NLP/TrialGPT), an open-source clinical trial matching system developed by the National Center for Biotechnology Information (NCBI). This page explains the relationship between the two systems, the key differences in GARDIAN's approach, and the results of our comparative validation.

## Based on TrialGPT

TrialGPT introduced a novel approach to clinical trial matching that uses large language models at every stage of the pipeline. Rather than relying solely on keyword search or manual curation, TrialGPT showed that LLMs can:

1. Extract structured search conditions from free-text clinical notes
2. Retrieve relevant trials through hybrid search (BM25 + semantic)
3. Evaluate individual eligibility criteria against patient information
4. Produce relevance and eligibility scores with explanations

GARDIAN reimplements this same five-stage pipeline. We use the same LLM prompt structures for keyword extraction, criterion-level matching, and ranking. TrialGPT is included as a git submodule in the GARDIAN repository, providing reference data, benchmark datasets, and validation targets.

## Key Differences

While GARDIAN shares TrialGPT's workflow design, several aspects differ significantly — reflecting GARDIAN's role as a production system for rare disease patients rather than a research prototype.

### Full Corpus Coverage

This is the most fundamental difference between the two systems.

TrialGPT's published benchmarks were evaluated against **small, curated trial corpora**:

| Benchmark | TrialGPT Corpus Size |
|-----------|---------------------|
| SIGIR | 3,620 trials |
| TREC 2021 | 26,148 trials |
| TREC 2022 | 26,580 trials |

GARDIAN searches the **entire ClinicalTrials.gov registry** — over **570,000 trials**.

This is a deliberate design choice. Rare disease patients cannot rely on pre-filtered trial subsets. A curated corpus might exclude a newly registered trial, a trial in an adjacent therapeutic area, or a basket trial that happens to include their condition. GARDIAN's whole-registry approach ensures nothing is missed.

### Database-Native Search

TrialGPT uses in-memory search tools:

- **rank_bm25** — A Python library that builds BM25 indexes in memory
- **FAISS** — Facebook's library for in-memory vector similarity search

GARDIAN uses PostgreSQL-native search extensions:

- **ParadeDB pg_search** — BM25 full-text search as a PostgreSQL extension
- **pgvector** — Vector similarity search with HNSW indexing in PostgreSQL

The database-native approach enables persistent indexing (no need to rebuild on restart), concurrent access from multiple API workers, and incremental updates as new trials are ingested — all essential properties for a production system.

### Live Data Pipeline

TrialGPT operates on static dataset snapshots. To update the trial corpus, the entire dataset must be re-downloaded and re-indexed.

GARDIAN maintains a live connection to ClinicalTrials.gov through API v2. A daily sync process:

- Fetches new and modified trials
- Detects changes using SHA-256 content hashing
- Preserves version history (previous versions are retained, not overwritten)
- Transforms new trials into the search-optimized format
- Computes embeddings for new entries

This means GARDIAN's corpus stays current without manual intervention.

### Production Application

TrialGPT is a research codebase — a collection of Python scripts designed to be run from the command line to process benchmark datasets and produce evaluation results.

GARDIAN is a deployed web application with:

- A **REST API** (FastAPI) with structured endpoints for search, matching, and statistics
- A **web interface** (Next.js) for interactive trial search and patient matching
- **Real-time progress updates** via WebSocket during the matching pipeline
- **Kubernetes deployment** with health checks, auto-scaling, and shared infrastructure

### Rare Disease Focus

TrialGPT was designed as a general-purpose clinical trial matching system. GARDIAN is specifically built for the [GARD](https://rarediseases.info.nih.gov/) (Genetic and Rare Diseases Information Center) program at NCATS, targeting rare disease patient populations where finding relevant trials is most challenging.

## Comparative Validation

We validated GARDIAN's pipeline against the same benchmark datasets used in TrialGPT's published evaluation: SIGIR, TREC 2021, and TREC 2022. These datasets provide ground-truth relevance judgments (qrels) that indicate which trials are relevant to each patient query.

### Retrieval Recall

Retrieval recall measures the proportion of known-relevant trials that the system successfully retrieves. The table below compares TrialGPT's recall (searching its curated corpus) against GARDIAN's recall (searching the full 570,000+ trial database):

| Dataset | TrialGPT Recall | GARDIAN Recall | Corpus Ratio |
|---------|-----------------|----------------|--------------|
| SIGIR | 98.8% (3.6K corpus) | ~54% (570K corpus) | 157x larger |
| TREC 2021 | 95.6% (26K corpus) | ~84% (570K corpus) | 22x larger |
| TREC 2022 | 91.9% (26K corpus) | ~84% (570K corpus) | 21x larger |

### Understanding the Recall Gap

The recall difference is primarily explained by **corpus size**, not pipeline quality.

Consider a search for "diabetes": in a corpus of 3,620 trials, retrieving the top 2,000 results covers more than half of all trials — the relevant ones are very likely included. In a corpus of 570,000 trials, the same top-2,000 retrieval represents only 0.35% of the corpus, and thousands of other trials mentioning "diabetes" compete for those spots.

This is the needle-in-a-haystack problem at scale. GARDIAN mitigates it through deep retrieval (2,000 results per condition per method), condition-weighted fusion, and hybrid search — but the fundamental challenge of searching a corpus 20–150x larger means recall on these benchmarks will naturally be lower.

Crucially, this lower benchmark recall is a trade-off for **complete coverage**. TrialGPT's high recall numbers reflect searching within a pre-selected subset. GARDIAN's lower recall reflects searching *everything* — which means it can find trials that were never in TrialGPT's curated corpus at all.

### Matching and Ranking Quality

Matching and ranking quality are **comparable** between the two systems. Both use the same LLM-based approach with identical prompt structures for criterion-level matching and score aggregation. The quality of these stages depends on the LLM's reasoning ability rather than the retrieval infrastructure.

### Validation Test Suite

GARDIAN includes a comprehensive validation test suite with **35 tests** across the three benchmark datasets, covering:

- Reference data format integrity
- Retrieval recall against ground-truth qrels
- Ranking correlation (Spearman) between predicted and ground-truth relevance
- Matching format consistency (valid labels, both criterion types present)
- Cross-dataset consistency (keyword, retrieval, matching, and ranking stages aligned)

All 35 tests pass across SIGIR, TREC 2021, and TREC 2022.

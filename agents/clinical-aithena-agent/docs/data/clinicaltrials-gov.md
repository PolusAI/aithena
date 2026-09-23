# ClinicalTrials.gov Integration

GARDIAN ingests the complete ClinicalTrials.gov registry and keeps it current through daily automated synchronization. This page describes what data is collected, how it's stored, and how the system stays up to date.

## Data Source

ClinicalTrials.gov is a database of clinical studies conducted around the world, maintained by the U.S. National Library of Medicine. It contains over 570,000 registered trials covering a wide range of conditions, interventions, and study types.

GARDIAN uses the **ClinicalTrials.gov API v2** to fetch trial data. The API provides structured JSON responses with detailed information about each study, including:

- **Protocol section** — Title, summary, study design, conditions, interventions, eligibility criteria, contacts, and locations
- **Results section** — Outcomes, adverse events, and participant flow (when available)
- **Derived section** — Computed fields like condition meshes, intervention meshes, and study classifications

## Two-Layer Storage

GARDIAN stores trial data in two complementary formats within PostgreSQL:

### Raw Layer — CTGovStudy

The raw data from ClinicalTrials.gov is preserved in full. Each study is stored as a set of JSONB columns that mirror the API's response structure. This preserves every field exactly as provided, ensuring no information is lost during ingestion.

Key stored sections include the protocol, results, derived data, and document metadata. Generated columns extract frequently queried fields (overall status, study type, title, enrollment count, dates, sponsor) for efficient filtering without parsing JSON.

### Search-Optimized Layer — TrialGPTStudy

For retrieval and matching, raw studies are transformed into a search-optimized format. Each transformed trial contains:

- **Title** — The brief title of the study
- **Full text** — A concatenation of the summary, inclusion criteria, and exclusion criteria
- **Metadata** — Structured fields including diseases, drugs, phase, enrollment, and separated inclusion/exclusion criteria
- **Embeddings** — Pre-computed MedCPT vector embeddings for the title and text (768 dimensions each)

This layer is indexed for both BM25 full-text search (via ParadeDB) and vector similarity search (via pgvector with HNSW indexes).

## Version Tracking

GARDIAN tracks changes to trials over time using SHA-256 content hashing:

1. When a trial is fetched from ClinicalTrials.gov, a hash is computed from its content
2. If the hash matches the most recent stored version, the trial is skipped (no changes)
3. If the hash differs, a new version is inserted with `is_latest=True` and the prior version is marked `is_latest=False`

This approach means:

- **Incremental updates** are fast — only changed trials are written
- **Version history** is preserved — previous versions of each trial are retained in the database
- **No data loss** — even if ClinicalTrials.gov removes or modifies a trial, the historical record persists

## Daily Synchronization

In the Kubernetes deployment, a CronJob runs daily to keep the corpus current. The synchronization pipeline performs three steps:

1. **Update** — Fetch all studies from ClinicalTrials.gov API v2, inserting new versions for any trials that have changed
2. **Transform** — Convert newly updated raw studies into the search-optimized format
3. **Embed** — Compute MedCPT embeddings for any new or updated trials

The entire process is incremental — only trials that have actually changed since the last sync are processed, keeping runtime and resource usage proportional to the rate of change rather than the total corpus size.

## Current Corpus

As of the latest sync, GARDIAN's database contains approximately:

- **570,000+** raw trial records from ClinicalTrials.gov
- **570,000+** search-optimized trial records
- **324,000+** trials with computed MedCPT embeddings (embedding coverage continues to grow)

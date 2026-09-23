# GARDIAN

**GARDIAN** (GARD Intelligent Association Network) is a clinical trial matching system designed specifically for rare diseases. Built on the [Aithena](https://github.com/PolusAI/aithena) platform, it helps patients and researchers find relevant clinical trials from the full ClinicalTrials.gov registry.

## The Problem

Patients with rare diseases face a unique challenge when searching for clinical trials. With over 570,000 registered trials on ClinicalTrials.gov, finding the right match requires understanding complex medical terminology, eligibility criteria, and disease classifications. Manual search is time-consuming and error-prone — particularly for rare diseases where relevant trials may be few and scattered across different therapeutic areas.

## What GARDIAN Does

GARDIAN provides two core capabilities:

- **Trial Search**: Browse and search the complete ClinicalTrials.gov database with real-time statistics on trials, conditions, phases, and interventions.

- **AI-Powered Patient Matching**: Given a patient's clinical note, GARDIAN identifies the most relevant clinical trials, explains *why* each trial matches, and assesses the patient's likely eligibility against each trial's inclusion and exclusion criteria.

The matching pipeline uses large language models to analyze clinical notes, extract medical conditions, retrieve candidate trials through hybrid search, and evaluate eligibility at the individual criterion level — producing detailed, explainable results.

## Key Features

- **Full corpus coverage** — Searches all 570,000+ trials on ClinicalTrials.gov, not a curated subset
- **Daily data sync** — Automatically updated from the ClinicalTrials.gov API to stay current
- **Hybrid retrieval** — Combines keyword search (BM25) with semantic search (MedCPT embeddings) for comprehensive trial discovery
- **Criterion-level matching** — Each inclusion and exclusion criterion is evaluated individually, with explanations
- **Relevance and eligibility scoring** — Trials are ranked by both clinical relevance (0–100) and eligibility assessment
- **Real-time progress** — Live status updates during the matching process so users know what's happening
- **Rare disease focus** — Designed for the [GARD](https://rarediseases.info.nih.gov/) (Genetic and Rare Diseases Information Center) program at NCATS

## Built On

GARDIAN's architecture is inspired by [Ask Aithena](https://github.com/PolusAI/aithena), following the same design patterns and shared infrastructure: a Next.js frontend, a FastAPI backend agent, PostgreSQL for data storage, and shared platform services including RabbitMQ for messaging and LiteLLM for LLM access.

The patient matching workflow is based on [TrialGPT](https://github.com/NCBI-NLP/TrialGPT), an open-source clinical trial matching system from NCBI. GARDIAN reimplements TrialGPT's pipeline and extends it to work at production scale across the full ClinicalTrials.gov corpus. See the [TrialGPT Comparison](how-it-works/trialgpt-comparison.md) for a detailed analysis of how the two systems relate.

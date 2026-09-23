# Trial Retrieval

Trial retrieval is the stage that narrows the search from 570,000+ registered clinical trials down to a manageable set of candidates for detailed matching. GARDIAN uses a hybrid approach that combines two fundamentally different search strategies.

## Why Hybrid Search?

Medical language is inconsistent. A trial for "chronic lymphocytic leukemia" might not appear in a keyword search for "CLL." A trial studying "immunotherapy for hematologic malignancies" is relevant to a leukemia patient but shares few exact terms. Conversely, semantic search alone can miss trials that use highly specific terminology — rare disease names, gene mutations, or drug compounds — where exact matching is critical.

By combining keyword search and semantic search, GARDIAN catches trials that either method alone would miss.

## BM25 Keyword Search

GARDIAN uses ParadeDB's `pg_search` extension for BM25 full-text search directly within PostgreSQL. For each search condition, the system queries across multiple trial fields with different importance weights:

| Field | Boost | Rationale |
|-------|-------|-----------|
| Title | 3x | A condition in the title strongly indicates relevance |
| Metadata (diseases, drugs, summary) | 2x | Structured fields are high-signal |
| Full text (criteria, description) | 1x | Broader context, more noise |

This field-weighted approach ensures that a trial titled "Gene Therapy for Fabry Disease" ranks higher than one that merely mentions Fabry disease in a long exclusion list.

## Semantic Search

GARDIAN uses MedCPT embeddings for semantic search. MedCPT is a biomedical encoder trained on PubMed, meaning it understands medical concepts and their relationships. Each trial has pre-computed 768-dimensional vector embeddings stored in PostgreSQL via pgvector, with HNSW indexes for fast approximate nearest-neighbor search.

At query time, the patient's search conditions are encoded using MedCPT's query encoder, and the most similar trial embeddings are retrieved using cosine similarity.

This means a search for "blood cancer" can find trials about "hematologic malignancies" or "lymphoma" — terms that are semantically related but textually different.

## Reciprocal Rank Fusion

The results from BM25 and semantic search are combined using **Reciprocal Rank Fusion (RRF)**. RRF is a rank-based aggregation method that doesn't require scores to be on the same scale — it works purely with rank positions:

$$
\text{RRF}(d) = \sum_{r \in R} \frac{1}{\text{rank}_r(d) + k}
$$

Where $R$ is the set of ranked lists and $k$ is a smoothing constant (set to 20). A trial that appears at rank 1 in BM25 and rank 5 in semantic search receives a higher fused score than one at rank 50 in both — regardless of the raw similarity scores.

## Condition Weighting

Not all search conditions are equally important. The LLM generates conditions in priority order — the patient's primary diagnosis first, secondary conditions next, and less specific symptoms last. GARDIAN reflects this ordering in the scoring:

$$
\text{weight}(i) = \frac{1}{i + 1}
$$

The first condition contributes at full weight, the second at half, the third at one-third, and so on. This ensures that a trial matching the patient's primary rare disease ranks higher than one matching only a secondary symptom.

## Retrieval Depth

GARDIAN retrieves up to **2,000 results per condition per search method**. With up to 32 conditions and two methods, this means tens of thousands of candidate trials are scored before RRF selects the top results.

This deep retrieval is necessary because of the large corpus. When searching 570,000+ trials, relevant results can appear well beyond the first page of any single query. Searching deep per condition and then fusing across conditions and methods is what allows GARDIAN to maintain strong recall despite the enormous search space.

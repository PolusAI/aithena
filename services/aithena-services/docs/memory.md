# Memory and Vector Database Features

Vector database functionality is the primary focus of Aithena Services. This document explains how to use the memory features for storing, retrieving, and searching vector embeddings using PostgreSQL with the pgvector extension.

## Overview

The memory feature in Aithena Services provides:
- Efficient similarity search using cosine distance via `pgvector`
- Retrieval of full Work objects with metadata (title, abstract, authors, etc.)
- Filtering by language and publication year
- Article retrieval by DOI

## Supported Tables

The service is configured to allow search on specific tables to ensure security and schema compliance. Currently allowed tables include:

- `openalex.abstract_embeddings_arctic`

## Similarity Search Features

The `search_works` endpoint allows you to find works similar to a query vector.

### Filtering

You can narrow down search results using the following filters:

- **Language**: Filter by one or more languages (e.g., `["en", "de"]`). The service supports normalization of language codes and names (e.g., "English", "german", "zh-cn").
- **Publication Year**: Filter by a range of years using `start_year` and `end_year`.

### Response Format

The search results include detailed metadata:
- **Work ID**: The OpenAlex ID of the work
- **Title**: The title of the work
- **Abstract**: The abstract text
- **Publication Year**: Year of publication
- **DOI**: Digital Object Identifier
- **Language**: Language code
- **Authorships**: List of authors with their positions and IDs
- **Similarity Score**: A score from 0 to 1 indicating how similar the work is to the query vector (1 being identical).

## Article Lookup

You can directly retrieve article metadata using its DOI via the `get_article_by_doi` endpoint. This supports various DOI formats:
- `10.1234/example`
- `https://doi.org/10.1234/example`

## Performance Optimization

The service uses `asyncpg` for high-performance asynchronous database access. It also supports `ivfflat` index probes configuration via the `IVFFLAT_PROBES` environment variable to tune the speed/accuracy trade-off of vector searches.

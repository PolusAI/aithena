# API Reference for Aithena Services

This document describes the API endpoints provided by Aithena Services. Aithena Services focuses on vector memory operations, providing a robust interface for storing, retrieving, and searching vector embeddings.

## Base URL

When deployed using Docker Compose, Aithena Services is accessible through two URLs:

1. Direct access:
```
http://localhost:8000
```

2. Via LiteLLM passthrough (for integrated usage):
```
http://localhost:4000/memory
```

## Memory API Endpoints

### Vector Search

#### Search for Works

```
POST /memory/pgvector/search_works
```

Via LiteLLM passthrough:
```
POST /memory/pgvector/search_works
```

Perform a similarity search on the specified table using a vector and return work objects. Supports filtering by language and publication year.

**Request Body:**

```json
{
  "table_name": "openalex.abstract_embeddings_arctic",
  "vector": [0.1, 0.2, ...],
  "n": 10,
  "languages": ["en", "de"],
  "start_year": 2020,
  "end_year": 2024
}
```

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `table_name` | string | Name of the table to search in (must be an allowed table) | Required |
| `vector` | array of float | The vector to search for similar vectors | Required |
| `n` | integer | Number of similar vectors to return | 10 |
| `languages` | array of string | Optional list of language codes to filter by (e.g., "en", "fr") | null |
| `start_year` | integer | Optional minimum publication year (inclusive) | null |
| `end_year` | integer | Optional maximum publication year (inclusive) | null |

**Response:**

Returns a list of work objects that are most similar to the provided vector.

```json
[
  {
    "id": "https://openalex.org/W123456789",
    "title": "Example Title",
    "abstract": "Example abstract...",
    "publication_year": 2023,
    "doi": "https://doi.org/10.1234/example",
    "language": "en",
    "similarity_score": 0.95,
    "authorships": [
      {
        "author_position": "first",
        "author_id": "https://openalex.org/A123456789",
        "display_name": "Jane Doe"
      }
    ]
  }
]
```

### Article Retrieval

#### Get Article by DOI

```
POST /memory/pgvector/get_article_by_doi
```

Via LiteLLM passthrough:
```
POST /memory/pgvector/get_article_by_doi
```

Retrieve an article and its metadata using its DOI.

**Request Body:**

```json
{
  "doi": "10.1234/example"
}
```

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `doi` | string | The DOI of the article (can be just the ID or full URL) | Required |

**Response:**

Returns a list containing the matching work object (usually one).

## Integration with LiteLLM

While Aithena Services focuses on memory operations, it integrates with LiteLLM for a complete AI development environment. When deployed with Docker Compose, both services work together seamlessly.

### LiteLLM Passthrough Configuration

In the Docker Compose deployment, LiteLLM is configured with a passthrough endpoint that routes all requests from `/memory` to the Aithena Services API. This allows applications to use a single base URL (`http://localhost:4000`) for both LLM operations and memory operations.

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200 OK`: Request was successful
- `400 Bad Request`: Invalid input parameters (e.g., invalid table name, invalid DOI format)
- `500 Internal Server Error`: Server-side error

Error responses include a JSON body with a `detail` field containing the error message:

```json
{
  "detail": "Error message here"
}
```

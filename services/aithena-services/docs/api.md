# API Reference for Aithena Services

This document describes the API endpoints provided by Aithena Services. Aithena Services now focuses specifically on vector memory operations, providing a robust interface for storing, retrieving, and searching vector embeddings.

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

The LiteLLM passthrough enables seamless integration between LiteLLM and Aithena Services, allowing you to access memory functionality through the same host as your LLM operations.

## Memory API Endpoints

### Vector Search

#### Search for Similar Vectors

```
POST /memory/pgvector/search
```

Via LiteLLM passthrough:
```
POST /memory/pgvector/search
```

Search for similar vectors in a specified table using pgvector with cosine distance.

**Request Body:**

```json
{
  "table_name": "my_vectors",
  "vector": [0.1, 0.2, ...],
  "n": 10,
  "full": false
}
```

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `table_name` | string | Name of the table to search in | Required |
| `vector` | array of float | The vector to search for similar vectors | Required |
| `n` | integer | Number of similar vectors to return | 10 |
| `full` | boolean | Whether to return the full Work object | false |

**Response:**

Returns a list of similar vectors with their similarity scores.

#### Search for Work IDs

```
POST /memory/pgvector/search_work_ids
```

Via LiteLLM passthrough:
```
POST /memory/pgvector/search_work_ids
```

Search for work IDs using pgvector similarity search.

**Request Body:**

```json
{
  "table_name": "my_vectors",
  "vector": [0.1, 0.2, ...],
  "n": 10
}
```

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `table_name` | string | Name of the table to search in | Required |
| `vector` | array of float | The vector to search for similar vectors | Required |
| `n` | integer | Number of similar vectors to return | 10 |

**Response:**

Returns a list of work IDs that are most similar to the provided vector.

#### Search for Works

```
POST /memory/pgvector/search_works
```

Via LiteLLM passthrough:
```
POST /memory/pgvector/search_works
```

Perform a similarity search on the specified table using a vector and return work objects.

**Request Body:**

```json
{
  "table_name": "my_vectors",
  "vector": [0.1, 0.2, ...],
  "n": 10
}
```

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `table_name` | string | Name of the table to search in | Required |
| `vector` | array of float | The vector to search for similar vectors | Required |
| `n` | integer | Number of similar vectors to return | 10 |

**Response:**

Returns a list of work objects that are most similar to the provided vector.

## Integration with LiteLLM

While Aithena Services focuses on memory operations, it integrates with LiteLLM for a complete AI development environment. When deployed with Docker Compose, both services work together seamlessly.

### LiteLLM Passthrough Configuration

In the Docker Compose deployment, LiteLLM is configured with a passthrough endpoint that routes all requests from `/memory` to the Aithena Services API. This allows applications to use a single base URL (`http://localhost:4000`) for both LLM operations and memory operations.

The passthrough is configured in the LiteLLM `config.yaml` file:

```yaml
general_settings:
  pass_through_endpoints:
    - path: "/memory"
      target: "http://aithena-services:8000/memory"
```

This means you can access all Aithena Services memory endpoints through LiteLLM by simply prepending `/memory` to the path.

For LiteLLM endpoints and model access, refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/).

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200 OK`: Request was successful
- `400 Bad Request`: Invalid input parameters
- `500 Internal Server Error`: Server-side error

Error responses include a JSON body with a `detail` field containing the error message:

```json
{
  "detail": "Error message here"
}
```

## API Cross-Origin Resource Sharing (CORS)

Aithena Services has CORS enabled by default, allowing requests from any origin. This can be configured for production environments. 
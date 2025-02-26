# Memory and Vector Database Features

Vector database functionality is now the primary focus of Aithena Services. This document explains how to use the memory features for storing, retrieving, and searching vector embeddings using PostgreSQL with the pgvector extension.

## Overview

The memory feature in Aithena Services provides:
- Vector storage in PostgreSQL with pgvector
- Efficient similarity search using cosine distance
- Work object storage and retrieval for semantic search applications
- Integration with embedding models via LiteLLM (when used with the complete stack)

## Current Architecture

In the current architecture, Aithena Services is responsible for:
- Managing vector database connections
- Providing API endpoints for similarity search
- Handling vector search queries efficiently
- Returning properly formatted search results

## PGVector Setup

When using the Docker Compose deployment, pgvector is automatically set up and configured. The database is created with the pgvector extension installed.

If you're deploying the standalone memory service, you'll need to:
1. Install PostgreSQL
2. Install the pgvector extension:
   ```sql
   CREATE EXTENSION vector;
   ```
3. Configure your connection using environment variables (see [Environment Variables](env.md))

## Vector Tables

Before storing vectors, you need to create tables with the appropriate schema. Typically, this includes:
- A column for the vector (using the `vector` data type from pgvector)
- Additional metadata columns (e.g., text content, ID, timestamps)

### Example Table Schema

```sql
CREATE TABLE my_vectors (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding VECTOR(1536),  -- Dimension matches your embedding model
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Similarity Search

Aithena Services provides endpoints for similarity search (see the [API Reference](api.md) for details). The search uses cosine similarity by default, which measures the cosine of the angle between two vectors.

### How Similarity Search Works

1. Convert your query text to a vector using an embedding model (via LiteLLM or another service)
2. Call the Aithena Services API to search the database for vectors similar to your query vector
3. Retrieve the most similar items based on the cosine similarity score

### Performance Considerations

- Vector search performance depends on the database size and vector dimensions
- For large datasets, consider using indexes:
  ```sql
  CREATE INDEX my_vectors_embedding_idx ON my_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
  ```
- Optimize queries by limiting the number of results returned

## Work Objects

Aithena Services uses "Work" objects to represent vector entries with their associated metadata. A Work object typically includes:
- The vector itself
- Content text
- ID and other metadata
- Similarity score (when returned from a search)

### Example Work Object

```json
{
  "id": "123",
  "content": "Sample text that was embedded",
  "embedding": [0.1, 0.2, ...],
  "metadata": {
    "source": "document1",
    "created_at": "2023-01-01T12:00:00Z"
  },
  "similarity": 0.92
}
```

## Using Memory Features in Applications

### RAG (Retrieval-Augmented Generation) Pattern

A common use case for vector databases is implementing RAG applications:

1. **Indexing Phase**:
   - Split documents into chunks
   - Generate embeddings for each chunk using an embedding model
   - Store embeddings and text in the vector database

2. **Retrieval Phase**:
   - Convert a user query to an embedding
   - Find similar vectors in the database using Aithena Services
   - Return the associated text chunks

3. **Generation Phase**:
   - Combine retrieved context with the original query
   - Send to an LLM for a contextually informed response

### Code Example

```python
import requests
from openai import OpenAI

# Configure the clients
litellm_client = OpenAI(
    api_key="anything",  # The key doesn't matter for local use
    base_url="http://localhost:4000/v1"
)

# Generate embeddings for our query
response = litellm_client.embeddings.create(
    model="nomic-embed-text",
    input="What is vector search?"
)
query_vector = response.data[0].embedding

# Use Aithena Services to search for similar content
search_response = requests.post(
    "http://localhost:8000/memory/pgvector/search",
    json={
        "table_name": "my_vectors",
        "vector": query_vector,
        "n": 5
    }
)

# Use the retrieved information
similar_items = search_response.json()
context = "\n".join([item["content"] for item in similar_items])

# Optional: Generate a response using the retrieved context
chat_response = litellm_client.chat.completions.create(
    model="llama3.1",
    messages=[
        {"role": "system", "content": f"Use this context to answer the question: {context}"},
        {"role": "user", "content": "What is vector search?"}
    ]
)
```

## Advanced Features

### Hybrid Search

For better search results, consider implementing hybrid search:
- Combine vector similarity search with traditional text search
- Weight the results based on both semantic similarity and keyword matching

### Chunking Strategies

How you chunk your documents affects search quality:
- Smaller chunks provide more precise matching but less context
- Larger chunks provide more context but may dilute the relevance
- Consider semantic chunking based on document structure

## Troubleshooting

Common issues with vector database operations:

- **"Relation does not exist"**: Ensure the table has been created in the database
- **Dimension mismatch**: Verify that vector dimensions match between the table and your embeddings
- **Performance issues**: Consider adding appropriate indexes for large datasets
- **Connection errors**: Check your PostgreSQL connection settings in the environment variables 
# Filtering Works

When searching for similar works using the vector search API (`/memory/pgvector/search_works`), you can apply filters to narrow down the results based on metadata. This document explains the available filters and how to use them.

## Available Filters

The search endpoint supports filtering by:
1. **Language**: One or more languages
2. **Publication Year**: A range of years (start and/or end)

These filters are applied in the `WHERE` clause of the SQL query, ensuring that only works meeting your criteria are considered for similarity ranking.

### 1. Language Filtering

You can filter works by providing a list of language codes. The system automatically normalizes common language names to their ISO codes.

**Parameter:** `languages` (list of strings)

#### Supported Languages

The following language codes are supported:
- `en` (English)
- `de` (German)
- `es` (Spanish)
- `ja` (Japanese)
- `fr` (French)
- `zh-cn` (Chinese Simplified)
- `zh-tw` (Chinese Traditional)
- `ko` (Korean)
- `pt` (Portuguese)
- `ru` (Russian)
- `it` (Italian)
- `pl` (Polish)
- `nl` (Dutch)

#### Normalization

You can pass language names or variations, and the system will normalize them to the correct code. For example:
- "English", "english", "ENGLISH" -> `en`
- "German", "Deutsch" -> `de`
- "Chinese", "chinese-simplified" -> `zh-cn`

#### Example Request

```json
{
  "table_name": "openalex.abstract_embeddings_arctic",
  "vector": [0.1, 0.2, ...],
  "languages": ["en", "German", "français"]
}
```

This request will search for works in English (`en`), German (`de`), or French (`fr`).

### 2. Publication Year Filtering

You can filter works by their publication year using a start year, an end year, or both.

**Parameters:**
- `start_year` (integer): Minimum publication year (inclusive)
- `end_year` (integer): Maximum publication year (inclusive)

#### Logic
- If only `start_year` is provided: Returns works published in `start_year` or later.
- If only `end_year` is provided: Returns works published in `end_year` or earlier.
- If both are provided: Returns works published between `start_year` and `end_year` (inclusive).

#### Example Requests

**Works from 2023 onwards:**
```json
{
  "table_name": "openalex.abstract_embeddings_arctic",
  "vector": [0.1, 0.2, ...],
  "start_year": 2023
}
```

**Works between 2020 and 2022:**
```json
{
  "table_name": "openalex.abstract_embeddings_arctic",
  "vector": [0.1, 0.2, ...],
  "start_year": 2020,
  "end_year": 2022
}
```

## Combining Filters

You can combine filters to create more specific queries. All conditions must be met (AND logic), but within the `languages` filter, any of the listed languages matches (OR logic).

**Example:**
Find works in English or German published between 2020 and 2024.

```json
{
  "table_name": "openalex.abstract_embeddings_arctic",
  "vector": [0.1, 0.2, ...],
  "languages": ["en", "de"],
  "start_year": 2020,
  "end_year": 2024
}
```

This generates a query equivalent to:
```sql
WHERE w.language = ANY(['en', 'de'])
  AND w.publication_year >= 2020
  AND w.publication_year <= 2024
```


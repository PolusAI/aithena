# Ask AIthena MCP Server

A Model Context Protocol (MCP) server that provides access to scientific literature search and AI-powered question answering capabilities. This server connects to the Ask AIthena API to deliver evidence-based answers using scientific articles from academic databases.

## Features

### Core Tools

- **Scientific Article Search** - Semantic search across scientific literature with advanced filtering
- **DOI-based Retrieval** - Direct article lookup using DOI identifiers
- **Query Optimization** - Transform natural language queries into search-optimized terms
- **Multi-tier AI Answering** - Three levels of AI-powered responses with varying accuracy and processing depth

### Search Capabilities

- **Language Filtering** - Support for multiple languages or all languages
- **Temporal Filtering** - Filter articles by publication year range
- **Configurable Results** - Specify the number of articles to retrieve
- **Semantic Similarity** - Advanced vector-based search for relevant content

### Answering Modes

- **Owl Mode** - Fast, direct answers based on retrieved articles
- **Shield Mode** - Enhanced accuracy with document reranking
- **Aegis Mode** - Maximum precision with rigorous relevance filtering

## Installation & Setup

### Prerequisites

- Python 3.12 or higher
- Access to Ask AIthena API endpoint

### Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install fastmcp httpx python-dotenv
```

### Configuration

1. Copy the environment template:
```bash
cp .env.sample .env
```

2. Configure the API endpoint in `.env`:
```env
ASKAITHENA_API_URL=http://localhost:8080
```

Replace `http://localhost:8080` with your actual Ask AIthena API URL.

### Running the Server

```bash
# Using the package script
ask-aithena-mcp

# Or directly with Python
python -m polus.aithena.ask_aithena_mcp.server
```

The server will start on HTTP transport at port 3283.

## Usage Examples

### Basic Article Search

```python
# Search for articles about machine learning
result = await get_articles(
    query="machine learning applications in healthcare",
    langs=['en'],
    n=10
)
```

### Advanced Search with Filters

```python
# Search recent articles in multiple languages
result = await get_articles(
    query="CRISPR gene editing therapeutic applications",
    langs=['en', 'es'],
    start_year=2020,
    end_year=2024,
    n=15
)
```

### Retrieve Article by DOI

```python
# Get specific article details
article = await get_article_by_doi(
    doi="10.1038/s41598-021-91234-y"
)
```

### Query Optimization

```python
# Transform conversational query into search-optimized form
optimized = await get_semantic_query(
    text="I'm a doctor and I need to know what is the best treatment for diabetes in patients with hypertension."
)
# Returns: "Optimal treatment protocols for diabetes in patients with comorbid hypertension."
```

### AI-Powered Answering

#### Owl Mode (Fast)
```python
# Quick evidence-based answer
answer = await answer_owl(
    query="What are the benefits of intermittent fasting?",
    langs=['en'],
    n=10
)
```

#### Shield Mode (Balanced)
```python
# More accurate answer with document reranking
answer = await answer_shield(
    query="What are the molecular mechanisms of Alzheimer's disease?",
    langs=['en'],
    start_year=2018,
    n=12
)
```

#### Aegis Mode (Maximum Accuracy)
```python
# Highest precision for critical questions
answer = await answer_aegis(
    query="What are the current safety profiles of mRNA vaccines?",
    langs=['en'],
    start_year=2020,
    n=20
)
```

## API Reference

### Tools

#### `get_articles`

Retrieve articles based on semantic similarity search.

**Parameters:**
- `query` (str): The search query, typically a question or topic
- `langs` (list[str], optional): Language codes (e.g., ['en', 'es']) or ['all']. Default: ['en']
- `start_year` (int, optional): Earliest publication year. Use -1 for no filter. Default: -1
- `end_year` (int, optional): Latest publication year. Use -1 for no filter. Default: -1
- `n` (int, optional): Number of articles to retrieve. Default: 10

**Returns:** JSON array of articles with title, OpenAlex ID, year, similarity score, and abstract.

#### `get_article_by_doi`

Retrieve a specific article using its DOI identifier.

**Parameters:**
- `doi` (str): DOI identifier (with or without 'https://doi.org/' prefix)

**Returns:** JSON array of matching articles (usually one, but may be multiple in edge cases).

#### `get_semantic_query`

Transform natural language into search-optimized queries.

**Parameters:**
- `text` (str): Natural language query to optimize

**Returns:** JSON object containing the optimized semantic query.

#### `answer_owl`

Generate evidence-based answers using Owl mode (fast processing).

**Parameters:**
- `query` (str): The question to answer
- `langs` (list[str], optional): Language filter. Default: ['en']
- `start_year` (int, optional): Year filter start. Default: -1
- `end_year` (int, optional): Year filter end. Default: -1
- `n` (int, optional): Number of source articles. Default: 10

**Returns:** JSON object with the generated answer and source citations.

#### `answer_shield`

Generate evidence-based answers using Shield mode (enhanced accuracy with reranking).

**Parameters:** Same as `answer_owl`

**Returns:** JSON object with the generated answer based on reranked, higher-quality sources.

#### `answer_aegis`

Generate evidence-based answers using Aegis mode (maximum accuracy with rigorous filtering).

**Parameters:** Same as `answer_owl`

**Returns:** JSON object with the most accurate answer based on thoroughly vetted sources.

### Prompts

The server also provides prompt generation tools (`prompt_owl`, `prompt_shield`, `prompt_aegis`) that return formatted prompts instead of complete answers, useful for integration with external language models.

## Architecture Overview

### Answering Modes Comparison

| Mode | Speed | Accuracy | Use Case |
|------|-------|----------|----------|
| **Owl** | Fast | Good | General questions, quick research |
| **Shield** | Medium | Better | Complex topics requiring accuracy |
| **Aegis** | Slower | Best | Critical research, medical/scientific precision |

### Processing Pipeline

1. **Query Processing** - Natural language query is processed and optimized
2. **Article Retrieval** - Semantic search finds relevant scientific articles
3. **Document Filtering** - (Shield/Aegis) Additional relevance filtering and reranking
4. **Answer Generation** - AI model generates response based on filtered articles
5. **Citation Integration** - Sources are properly attributed in the response

### Language Support

The server supports filtering by:
- Specific languages using ISO 639-1 codes: `['en', 'es', 'fr']`
- Language names in English: `['English', 'Spanish', 'French']`
- All languages: `['all']`

### Year Filtering

- Use specific years: `start_year=2020, end_year=2024`
- Open-ended ranges: `start_year=2020, end_year=-1` (2020 to present)
- No filtering: `start_year=-1, end_year=-1`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ASKAITHENA_API_URL` | Ask AIthena API endpoint URL | `http://localhost:8080` |

### API Requirements

The server requires a running Ask AIthena API instance that provides the following endpoints:
- `/get-articles` - Article search
- `/get-article-by-doi` - DOI-based retrieval
- `/get-semantic-query` - Query optimization
- `/answer-owl`, `/answer-shield`, `/answer-aegis` - AI answering
- `/prompt-owl`, `/prompt-shield`, `/prompt-aegis` - Prompt generation

Ensure your API instance is properly configured and accessible before starting the MCP server.

# Docker Compose Setup

## What You'll Build

Deploying these services creates a complete AI development environment that gives you the flexibility to use both local and cloud-based large language models through a unified API. This setup enables you to build sophisticated AI applications with features like vector search, long-term memory, and conversational capabilities, all while maintaining control over your data and reducing dependency on external APIs. The OpenAI-compatible interface allows seamless integration with existing tools and libraries, making it easy to switch between local open-source models and commercial cloud providers as needed for your specific use case, privacy requirements, or budget constraints.

This guide helps you set up an AI development environment with the following components:

![LiteLLM Architecture Diagram](resources/architecture.svg)

## What These Services Do

* **litellm**: Provides an OpenAI-compatible API for accessing both local and cloud LLMs
* **pgvector**: A PostgreSQL database with an extension that enables vector operations for AI embeddings storage
* **ollama**: Runs open-source LLMs (like Llama, Mistral, etc.) locally on your machine
* **aithena-services**: Backend for vector operations and memory functions
* **litellm_db**: Database for storing LiteLLM configuration and usage data

## Detailed Setup Guide

### 1. Configure Environment Variables

First, you'll create a `.env` file to configure the services:

**What to do:**
1. In the same directory as your `compose.yml` file, copy `.env.sample` to `.env`
2. Edit the `.env` file with your preferred settings:

```bash
# Paths - Set these to your desired data storage locations
OLLAMA_DATA_PATH=/path/to/your/ollama/data  # e.g., /Users/yourname/.ollama
PGVECTOR_DATA_PATH=./pgdata  # This is relative to your compose.yml location

# Database passwords - Change these to secure passwords
PGVECTOR_PASSWORD=change_this_password
LITELLM_DB_PASSWORD=change_this_password

# LLMs API Keys - Add only the ones you plan to use
# OpenAI - Required for OpenAI and GPT models
OPENAI_API_KEY=your_openai_key_here
# Azure API - Required only if using Azure OpenAI
AZURE_API_BASE=your_azure_endpoint
AZURE_API_VERSION=2024-02-01
AZURE_API_KEY=your_azure_key
# Anthropic - Required for Claude models
ANTHROPIC_API_KEY=your_anthropic_key
# Groq - Required for Groq-hosted models
GROQ_API_KEY=your_groq_key
```

**IMPORTANT NOTES:**
* You only need API keys for services you plan to use
* For local-only usage with Ollama, you can leave all API keys blank
* Never put quotation marks around values in the `.env` file:
  * ❌ WRONG: `OPENAI_API_KEY="sk-1234"`
  * ✅ CORRECT: `OPENAI_API_KEY=sk-1234`

### 2. Configure LiteLLM

Next, set up the LiteLLM configuration:

**What to do:**
1. In the same directory as your `compose.yml` file, copy `config_sample.yaml` to `config.yaml`
2. If needed, edit `config.yaml` to add/modify models

**IMPORTANT:** The `config.yaml` file is mounted directly to the Docker container. This means:
- Any changes you make to this file will be automatically picked up when you restart the container
- You can update your model configurations, add new models, or modify settings without rebuilding the container
- To apply changes, just edit `config.yaml` and run `docker compose restart litellm`

The `config.yaml` file defines which models are available and how they connect. Here's an example of the model configuration format:

```yaml
model_list:
  - model_name: llama3.1           # This is the name you'll use in API calls
    litellm_params:
      model: ollama_chat/llama3.1:latest  # The actual model identifier
      api_base: os.environ/OLLAMA_HOST    # Connects to your Ollama container
    model_info:
      supports_function_calling: true     # Optional metadata

  - model_name: gpt-4o            # Cloud model example
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY  # Uses your OpenAI API key
```

**⚠️ IMPORTANT:** The `config.yaml` file also includes pass-through endpoint configurations that enable communication between services. Do NOT modify this section unless you know exactly what you're doing:

```yaml
general_settings:
  pass_through_endpoints:
    - path: "/ollama/ps"
      target: "http://ollama:11434/api/ps"
    - path: "/ollama/pull"
      target: "http://ollama:11434/api/pull"
    - path: "/ollama/delete"
      target: "http://ollama:11434/api/delete"
    - path: "/ollama/list"
      target: "http://ollama:11434/api/tags"
    - path: "/memory"
      target: "http://aithena-services:8000/memory"
```

These endpoints are essential for easy management of local models and for proper communication between services. Modifying them incorrectly can break the system's functionality.

### 3. Run Docker Compose

Now you're ready to start the services:

**What to do:**
1. Open a terminal or command prompt
2. Navigate to the directory containing your `compose.yml` file
3. Run one of these commands:
   - `docker compose up -d` (runs in background)
   - `docker compose up` (shows logs in real-time)

The first time you run this, it may take several minutes to download and build all the images.

### 4. Download and Test a Model

After the services are running, download a model and test it:

**Download a small model first:**
```bash
curl -XPOST localhost:4000/ollama/pull -H 'content-type: application/json' -d '{"model": "llama3.2:1b"}'
```

**Test that the model works:**
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [{"role": "user", "content": "If a pirate and a bear got in a fight over the last jar of peanut butter, who would win and why?"}]
  }'
```

## Using the Services

### List Available Models

To see all configured models:

```bash
curl http://localhost:4000/v1/model/info
```

### Chat with Models using the OpenAI-compatible API

LiteLLM provides an OpenAI-compatible API at `http://localhost:4000/v1`. This means you can use any OpenAI client library by pointing it to your local server.

#### Python Example:

```python
import openai

# Configure the client to use your local LiteLLM server
client = openai.OpenAI(
    api_key="anything",  # The key doesn't matter for local use
    base_url="http://localhost:4000/v1"
)

# Chat with a model
response = client.chat.completions.create(
    model="llama3.1",  # Use any model you've downloaded
    messages=[
        {"role": "user", "content": "Could a bear navigate a pirate ship to the edge of a flat Earth? What supplies would they need, especially regarding peanut butter provisions?"}
    ]
)

print(response.choices[0].message.content)
```

#### JavaScript Example:

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'anything', // The key doesn't matter for local use
  baseURL: 'http://localhost:4000/v1',
});

async function main() {
  const response = await openai.chat.completions.create({
    model: 'llama3.1',
    messages: [
      { role: 'user', content: 'Write a short sea shanty about a pirate bear who discovered the world is round while searching for the legendary peanut butter island' }
    ],
  });

  console.log(response.choices[0].message.content);
}

main();
```

### Streaming Responses

To receive responses as they're generated (streaming):

```python
# Python streaming example
response = client.chat.completions.create(
    model="llama3.1",
    messages=[
        {"role": "user", "content": "You're a pirate scientist trying to explain why the Earth is definitely NOT flat to your skeptical crew. Use your most convincing pirate dialect and mention your bear first mate who loves peanut butter."}
    ],
    stream=True  # Enable streaming
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## Troubleshooting

### Common Issues and Solutions

**Issue: Services Won't Start**
- Check Docker is running
- Verify ports 4000, 11434, and 5432 aren't already in use
- Ensure your `.env` file doesn't have quotes around values

**Issue: Can't Pull Models**
- Check disk space (models can be large)
- Ensure the Ollama container is running: `docker ps | grep ollama`
- Try with a smaller model first (e.g., `llama3.2:1b`)

**Issue: Model Returns Errors or Poor Results**
- Verify model was fully downloaded
- Check you have sufficient RAM for the model size
- Try a different model or a smaller variant

**Issue: API Key Not Working**
- Ensure no quotes in `.env` file
- Verify API key is valid and has proper permissions
- Check the model requires that specific API

## Security Considerations

For production use:

1. **Change All Default Passwords** in your `.env` file
2. **Set Up Authentication** with a master key:
   ```
   LITELLM_MASTER_KEY=sk-your-secure-master-key
   ```
3. **Generate User-Specific API Keys**:
   ```bash
   curl -X POST "http://localhost:4000/key/generate" \
     -H "Authorization: Bearer your-secure-master-key" \
     -H "Content-Type: application/json" \
     -d '{"models": ["llama3.1"], "metadata": {"user": "username"}}'
   ```
4. **Use TLS/HTTPS** in production environments
5. **Limit Access** to the Docker network
6. **Regularly Update** all containers

## Advanced Features

### Vector Search with PGVector

PGVector enables similarity search capabilities for building RAG applications:

1. Create a vector table in the PostgreSQL database
2. Store embeddings in the table
3. Query similar vectors through the API

For details on using the memory API and PGVector features, see [Memory and Vector Database Features](memory.md) and [API Reference](api.md).

### LiteLLM UI Dashboard

A web UI dashboard is available at: `http://localhost:4000/ui`

This dashboard allows you to:
- View usage statistics
- Generate and manage API keys
- Test models directly in the browser
- Set rate limits and budgets

## Where to Get Help

- LiteLLM Documentation: [https://docs.litellm.ai/docs/](https://docs.litellm.ai/docs/)
- Ollama Documentation: [https://ollama.com/library](https://ollama.com/library)
- PGVector Documentation: [https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector) 
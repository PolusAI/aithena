# AIthena Services
## Model Configuration

It is through the `config.json` file that users will made the REST API of AIthena Services aware of which models are available.
It is through setting environment variables that users will make Aithena-Services aware of which models are available. Models include chat and embedding models.
# .env
1. Rename `.env-sample` to `.env`
2. Replace the values of the environment variables with the correct values

Your .env file should **only** contain variables of the services you want to use. For example, if you will not use OpenAI, you must remove (or comment out) the `OPENAI_API_KEY` variable.

### Docker
*IMPORTANT (Only if using `.env` file for Docker)* : Do not include quotation marks (") in your .env file, for example:
```
AZURE_OPENAI_API_KEY="abc123" # this will not work
AZURE_OPENAI_API_KEY=abc123 # this is correct
```


## Ollama
You need to set up the environment variable `OLLAMA_HOST` with the correct url where you are serving Ollama. For example, if you use the default url, you would need to set up
```
OLLAMA_HOST="http://localhost:11434"
```

**Aithena-Services will automatically scan the Ollama server to check which models are available. This includes chat and embed models.**


## OpenAI
You need to set up the environment variable `OPENAI_API_KEY` with the value of your API key.
```
OPENAI_API_KEY="sk-projHDFIADFHDFIA"
```
**Aithena-Services will automatically scan the OpenAI server to check which models are available. This includes only chat models. Support for OpenAI embedding models has not been implemented.**

## Azure OpenAI
Check [AzureEnv](AzureEnv.md)
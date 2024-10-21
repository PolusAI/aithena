# Aithena Chat Agent 0.1.0-dev4

A generic chat agent to interact with chat models in the Aithena framework.

## Configure 

Rename `variables-sample.env` to `.env` and configure according to your deployment.


## Environment Variables

* `AITHENA_SERVICES_URL` *Required*: URL of Aithena-Services API, e.g 'http://localhost:8000'
* `AITHENA_CHAT_PROMPT` *Optional*: a system prompt for all conversations in the dashboard. If this variable is not specified, the following prompt will be used:
* `AITHENA_CHAT_DEFAULT_MODEL` *Optional*: default model that will be selected when starting the dashboard. If the value of this environment variable is a model that is not available in Aithena-Services, this variable will be ignored.
```
PROMPT_DEFAULT = """
You are a helpful assistant named Aithena.
Respond to users with witty, entertaining, and thoughtful answers.
User wants short answers, maximum five sentences.
If user asks info about yourself or your architecture,
respond with info about your LLM model and its capabilities.
Do not finish every sentence with a question.
If you ask a question, always include a question mark.
Do not introduce yourself to user if user does not ask for it.
Never explain to user how your answers are.
"""
```

* `AITHENA_CHAT_CONTEXT_WINDOW_SIZE` *Optional*: context window in tokens. Default is 2048. This is used as the initial/default value of the input box.
# Ask Aithena (v0.1.2-dev0)

The AskAithena agent is a high level services that implements the basic `ask` rag function.
Provided with a question or a query, it will retrieve relevant documents from a database
and feed those document to a chat model to generate a response.

See `agents/ask-aithena/src/polus/aithena/ask_aithena/config.py` for available environment variables
to help configure and customize the agent.

# Docker Image

Build the container:
`./build-docker.sh`

Start the container :
`docker run -it --rm -p8000:8000 polusai/ask-aithena-agent:${VERSION}(-arm64)`

Test:

`curl http://0.0.0.0:8000`

> {"status":"ask-aithena agent is running"}

# Tests

`pytest` or `poetry run pytest`

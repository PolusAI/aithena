# Ask Aithena (v0.1.2-dev1)

The AskAithena agent is a high level services that implements the basic `ask` rag function.
Provided with a question or a query, it will retrieve relevant documents from a database
and feed those document to a chat model to generate a response.

See `agents/ask-aithena/src/polus/aithena/ask_aithena/config.py` for available environment variables to help configure and customize the agent.

# Docker Image

Build the container:
`./build-docker.sh`

Start the container :
`docker run -it --rm -${ASK_AITHENA_AGENT_PORT}:8000 polusai/${ASK_AITHENA_AGENT_IMAGE_NAME}:${ASK_AITHENA_AGENT_VERSION}`

Test:

`curl http://0.0.0.0:${ASK_AITHENA_AGENT_PORT}`

> {"status":"ask-aithena agent is running"}

# Tests

`pytest` or `poetry run pytest`


# Example Deployment

For our example deployment, we will use docker to set up our all infrastructure.

Follow instructions to deploy [aithena services](../../services/aithena-services/README.md#example-deployment)

We will also need to deploy qdrant.

`docker run -p ${DB_PORT}:6333 --name qdrant --net ${DOCKER_NETWORK} qdrant/qdrant:latest`

Then you can deploy the agent:

```shell
docker run -it --rm -p${ASK_AITHENA_AGENT_NODEPORT}:8000 --env AITHENA_SERVICE_URL=${AITHENA_SERVICE_URL} --env DB_HOST=${DB_HOST} --env DB_PORT=${DB_PORT} --env DOC_COLLECTION=${DOC_COLLECTION}  --net ${DOCKER_NETWORK} --name ask-agent polusai/ask-aithena-agent:${ASK_AITHENA_AGENT_IMAGE_VERSION}
```

# Test

```shell
curl -X POST http://localhost:${ASK_AITHENA_AGENT_NODEPORT}/ask -H "Content-Type: application/json" -d '{"query": "What is the capital of France?"}'
```



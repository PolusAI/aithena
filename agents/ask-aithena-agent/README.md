# Ask Aithena (v0.1.2-dev1)

The AskAithena agent is a high level services that implements the basic `ask` rag function.
Provided with a question or a query, it will retrieve relevant documents from a database
and feed those document to a chat model to generate a response.

See `agents/ask-aithena/src/polus/aithena/ask_aithena/config.py` for available environment variables
to help configure and customize the agent.

# Docker Image

Build the container:
`./build-docker.sh`

Start the container :
`docker run -it --rm -p8000:8000 polusai/ask-aithena-agent:${VERSION}`

Test:

`curl http://0.0.0.0:8000`

> {"status":"ask-aithena agent is running"}

# Tests

`pytest` or `poetry run pytest`

## Example Deployment

For our example deployment, we will use docker to set up our all infrastructure.

Follow instructions to deploy [aithena services](../../services/aithena-services/README.md#example-deployment)

We will also need to deploy qdrant.

`docker run -p 6333:6333 --name qdrant --net aithena-net qdrant/qdrant:latest`

Then you can deploy the agent:

```shell
VERSION=0.1.2-dev1
AITHENA_SERVICE_URL=http://ais:9000
DB_HOST=qdrant
DB_PORT=6333
DOC_COLLECTION=example_db
docker run -it --rm -p8000:8000 --env AITHENA_SERVICE_URL=${AITHENA_SERVICE_URL} --env DB_HOST=${DB_HOST} --env DB_PORT=${DB_PORT} --env DOC_COLLECTION=${DOC_COLLECTION}  --net aithena-net --name ask-agent polusai/ask-aithena-agent:${VERSION}
```

Test





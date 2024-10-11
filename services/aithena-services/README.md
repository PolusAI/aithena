# aithena-services 0.1.1-dev0

Aithena-services provides a unified way to interact with many LLMs.

It uses llama-index to interact with several existing LLM backends:
- ollama
- openai
- azure_openai

The package can be used directly as a python client or can be deployed as a REST service.


## Configuration

This service is a client to existing LLM backends that must be deployed independently.
You will need to tell aithena services which backends it can talk to by defining a set of enviroment variables.
Available environment variables and how to configure aithena-services is described [here](docs/env.md)


## Example Deployment

They are many ways to deploy aithena services.
This section will describe steps by steps how to set up aithena services for testing purposes.

### Prerequisites

For simplicity, we will create a simple docker deployment.
We will create a docker network and deployed ollama and aithena services on this network.

```shell
DOCKER_NETWORK=aithena-net
docker create network ${DOCKER_NETWORK}
docker run -p 11434:11434 --net aithena-net  --name ollama ollama/ollama
```

Here we start the ollama container (the image will pulled if not present), give it the name ollama, and expose it to the network on port 11434.

We will deploy aithena services on port `9000`

```shell
PORT=9000
```

A simple way to deploy aithena services for testing is to use our existing docker image

```shell
OLLAMA_HOST=http://ollama:11434
docker run -it -p ${PORT}:80 --env OLLAMA_HOST=${OLLAMA_HOST}  --net ${DOCKER_NETWORK} --name ais polusai/aithena-services:0.1.1-dev0
```

Note that we configured aithena services to reach ollama at `http://ollama:11434` using the service exposed by the docker network.
Update the image version to match the current version.

### Configure ollama

The last thing we need to do is to pull the models we want to test.
This can be done directly through aithena services.

We will pull nomic-embed-text for embedding and llama3.1 for chat.

```shell
curl -X POST  http://0.0.0.0:${PORT}/ollama/pull/nomic-embed-text
curl -X POST  http://0.0.0.0:${PORT}/ollama/pull/llama3.1:latest
```

## Tests

Test embed:

```shell
curl -X POST  http://0.0.0.0:${PORT}/ollama/pull/nomic-embed-text
curl -X POST http://localhost:${PORT}/embed/nomic-embed-text/generate -d '"This is a test embedding"'
```

Test chat:

```shell
curl -X POST  http://0.0.0.0:${PORT}/ollama/pull/llama3.1:latest
curl -X POST http://localhost:${PORT}/chat/llama3.1/generate\?stream\=False -d '[{"role": "user", "content": "What is the capital of France?"}]'
```

## Development

It can be useful to deploy aithena service as a regular process.
This snippet assume that [poetry](https://python-poetry.org/) is available on your path.

```shell
cd services/aithena-services
python -m venv .venv
source .ven/bin/activate
poetry install
uvicorn --host 0.0.0.0 --port ${PORT}  main:app
```

## Building the docker image

TODO: FIX how we build the docker image.

Currently the image needs to be build from the top-level directory:

`cd services/aithena-services/src/aithena_services`
`./docker/build-docker.sh`

Make sure no .env file is present is `services/aithena-services/src/aithena_services` or this file will be committed with the image leaking your secrets and it will also prevent any later configuration attempt.

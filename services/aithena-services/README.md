# aithena-services 0.1.0-dev3

Aithena-services provide a unified way to interact with many llms.

It uses llama-index to interact with several existing llm backends:
- ollama
- openai
- azure_openai

The package can be used directly as a python client or can be deployed
as a rest service.

## Configuration

This service is a client to existing llm backends that must be deployed independently.
You will need to tell aithena services which backends it can talk to by defining a set of environment variables.
Available environment variables are in an [env file](.env-sample) and how to configure aithena-services is described [here](docs/env.md)


## Example Deployment

They are many ways to deploy aithena services.

Helm deployment charts are found [here](helm).

For testing purposes, the next section will describe steps by steps how to set up aithena services using only docker containers.


### Prerequisites

We will create a docker network and deploy ollama and aithena services on this network.

The following variables will be used:
Update the image version to match the current version.

```shell
DOCKER_NETWORK=aithena-net
OLLAMA_PORT=11434
OLLAMA_CONTAINER_NAME=ollama
AITHENA_SERVICES_PORT=9000
AITHENA_SERVICES_IMAGE=polusai/aithena-services:0.1.0-dev3
```

```shell

docker network create ${DOCKER_NETWORK}
docker run -p ${OLLAMA_PORT}:11434 --net ${DOCKER_NETWORK} --name ${OLLAMA_CONTAINER_NAME} ollama/ollama
```

Here we start the ollama container (the image will pulled if not present),
give it the name ollama, and expose it to the network on port 11434.

A simple way to deploy aithena services for testing is to use our existing docker image

```shell
OLLAMA_HOST=http://${OLLAMA_CONTAINER_NAME}:${OLLAMA_PORT}
docker run -it -p ${AITHENA_SERVICES_PORT}:80 --env OLLAMA_HOST=${OLLAMA_HOST}  --net ${DOCKER_NETWORK} --name ais ${AITHENA_SERVICES_IMAGE}
```

Note that we configured aithena services to reach ollama using the service exposed by the docker network.


### Configure ollama

The last thing we need to do is to pull the models we want to test.
This can be done directly through aithena services.

We will pull nomic-embed-text for embedding and llama3.1 for chat.

```shell
curl -X POST  http://0.0.0.0:${AITHENA_SERVICES_PORT}/ollama/pull/nomic-embed-text
curl -X POST  http://0.0.0.0:${AITHENA_SERVICES_PORT}/ollama/pull/llama3.1:latest
```

## Tests

Test embed:

```shell
curl -X POST http://localhost:${AITHENA_SERVICES_PORT}/embed/nomic-embed-text/generate -d '"This is a test embedding"'
```

Test chat:

```shell
curl -X POST http://localhost:${AITHENA_SERVICES_PORT}/chat/llama3.1/generate\?stream\=False -d '[{"role": "user", "content": "What is the capital of France?"}]'
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

|| TODO: FIX how we build the docker image.

Currently the image needs to be build from the top-level directory:

`cd services/aithena-services`
`./docker/build-docker.sh`

Make sure no .env file is present is `services/aithena-services/src/aithena_services`
or this file will be committed with the image leaking your secrets and
it will also prevent any later configuration attempt.

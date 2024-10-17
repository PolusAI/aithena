# Ollama

## Setup

Rename `.vars-sample` to `.vars`
Update values according to your deployment.

`source .vars`

## Install

### Install with Helm

mh install ollama helm  -n ${NAMESPACE}

## Configure

check it runs :

curl ${HOST}:${NODE_PORT}

Check available models: 
curl ${HOST}:${NODE_PORT}/api/tags


### Download models

```shell
curl ${HOST}:${NODE_PORT}/api/pull -d '{
  "name": "llama3.1"
}'
```

```shell
curl ${HOST}:${NODE_PORT}/api/pull -d '{
  "name": "nomic-embed-text"
}'
```


### check you can list the models

curl ${HOST}:${NODE_PORT}/api/tags


### Run queries

curl ${HOST}:${NODE_PORT}/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "This is a test embedding"
}'
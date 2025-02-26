# Ollama

This package contains several deployment scripts for ollama.

Currently:
- docker-compose script in `docker`
- a templated deployment with helm chart in `helm`
- a stateful sets deployment in `helm-alt`


## Setup

Rename `.vars-sample` to `.vars`
Update values according to your deployment.

`source .vars`

## Install


See `README.md` in each deployment directory for details.


## Configure

check ollama runs :

```curl ${HOST}:${NODE_PORT}```



Check available models: 

```curl ${HOST}:${NODE_PORT}/api/tags```



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

```curl ${HOST}:${NODE_PORT}/api/tags```


### Run queries

```shell
curl ${HOST}:${NODE_PORT}/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "This is a test embedding"
}'
```

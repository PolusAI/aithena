
# DEBUG HELM DEPLOYMENT

This is a step by step guide to deploy all elements of the stack individually.
This can be useful for debuggin purpose.


## ollama 

### install

mh install ollama .  --namespace test-aithena
curl http://0.0.0.0:32434


### download models

```shell
curl 0.0.0.0:32434/api/pull -d '{
  "name": "llama3.1"
}'
```

```shell
curl 0.0.0.0:32434/api/pull -d '{
  "name": "nomic-embed-text"
}'
```

### check you can list the models

curl http://0.0.0.0:32434/api/tags

=================
## qdrant

### Install

mh install qdrant .  --namespace test-aithena
curl http://0.0.0.0:32333


### copy data to qdrant collections.
(If qdrant has been run as priviledged user, you will
need to sudo)

cp -r collection /path/to/qdrant-data/collections/

### Check we can access the collection.

curl http://0.0.0.0:32333/collections


=====================
## aithena services

### create a secret

To deploy aithena services, we will need to create a secret first.

The secrets should contains tokens and possibly url that are used 

ex:
AZURE_OPENAI_API_KEY

kubectl create secret generic aithena-services-secret --from-file=/polus2/gerardinad/projects/aithena/helm/aithena-services-secret.yaml --namespace test-aithena

### configure extra env variable

Ex:
OLLAMA_HOST=http://service-ollama.test-aithena.svc.cluster.local:80

### install

mh upgrade ais . -n test-aithena

### Test

curl http://localhost:32080/chat/list

curl -X POST http://localhost:32080/chat/llama3.1/generate\?stream\=False -d '[{"role": "user", "content": "What is the capital of France?"}]'

curl -X POST http://localhost:32080/embed/nomic-embed-text/generate -d '"This is a test embedding"'


====================
## ask aithena agent

### configure 

  - name: AITHENA_SERVICE_URL
    value: "http://service-aithena-services-chart.default.svc.cluster.local:80"
  - name: EMBED_MODEL
    value: "nomic-embed-text"
  - name: CHAT_MODEL
    value: "gpt-4o"
  - name: DB_HOST
    value: "service-qdrant-chart.default.svc.cluster.local"
  - name: DB_PORT
    value: "6333"

### install

 mh install ask-aithena-agent . -n test-aithena

### test

curl -X POST http://localhost:32008/ask -H "Content-Type: application/json" -d '{"query": "What is the capital of France?"}'


=================
## ask aithena app

### configure


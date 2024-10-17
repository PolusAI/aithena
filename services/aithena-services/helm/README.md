## aithena services

Rename `.vars-sample` to `.vars` and `source .vars`

### create a secret

To deploy aithena services, we will need to create a secret first.
The secrets should contains tokens and possibly url that are used.
For none sensitive data, you can also use regular env variables.

Rename `aithena-services-secret-sample.yaml` to `aithena-services-secret.yaml`

If you already have a .env file with tokens you need to protect,
first base64_encode them and then add or update the secret file entries accordingly.

Then install the secret in the kubernetes cluster :

```shell
microk8s kubectl create secret generic aithena-services-secret --from-file=aithena-services-secret.yaml --namespace ${NAMESPACE}
```

### Update values.yaml

In particular update OLLAMA_HOST=$(echo http://${OLLAMA_SERVICE_NAME}.${NAMESPACE}.svc.cluster.local:${OLLAMA_PORT})


### install

```shell
mh upgrade ${RELEASE_NAME} . -n ${NAMESPACE}
``` 

### Test

```shell
curl http://localhost:${AITHENA_SERVICES_NODEPORT}/chat/list

curl -X POST http://localhost:${AITHENA_SERVICES_NODEPORT}/chat/llama3.1/generate\?stream\=False -d '[{"role": "user", "content": "What is the capital of France?"}]'

curl -X POST http://localhost:${AITHENA_SERVICES_NODEPORT}/embed/nomic-embed-text/generate -d '"This is a test embedding"'
```
# Deploy Aithena

* Make sure the helm plugin is enabled in your microk8s instance.
`microk8s status`

The following instructions describe how to deploy the whole infrastructure
in a single step.

Please see this [doc](docs/debug_helm.md) for how to deploy each 
component individually (for debugging purpose).

The following commands assume you are in the helm repository.

* Configure your deployment:
- rename `aithena-chart/values-sample.yaml` to `aithena-chart/values.yaml`
- update all values to match your deployment.

* Deploy:
```shell 
microk8s helm install aithena aithena-chart
```

## Configuration

we need to check that: 
- qdrant collections are set up.
- ollama models are available.
- aithena services are properly configured.
- aithena agent is properly configured.
- aithena app is properly configured.
- all services are reachable.



## Aithena Services


## Qdrant

we also need a database collection with `nomic-embed-text` embeddings.

For that we need either to:
i/ copy an existing collection to our new database.
ii/ deploy the ingestion pipeline that will populate the database with new arxiv records.


### Case 1 - Copy an existing collection

If you have already deployed the stack and have no sudo access, you will need to :
- deploy `debug/cp-data.yaml` with the correct mounted volume: 
    `microk8s kubectl apply -f debug/cp-data.yaml`
- get pod name:
    `pod_name=$(microk8s kubectl get pods | grep qdrant | awk '{print $1}')`
- copy data to mounted volume:
    `microk8s kubectl cp /path/to/nomic-embed-text-collection/* $(pod-name):/mnt/data/collections/arxiv_abstracts_nomic768`
(Note that arxiv_abstracts_nomic768 match the name provided in default configuration. Change if necessary to match your config.)
- kill and restart pod:
    `mkdd $(pod-name)`


### Case 2 - Start the ingestion pipeline

The ingestion pipeline is currently composed of two cron jobs:
- `get-arxiv-records`: download new arxiv records daily
- `embed-arxiv-records`: 
    - embed new abstracts
    - persist downloaded arxiv records + abstract embeddings to db

In order to run this pipeline, we first need to set up the database.

* Configure :
    - Navigate to the ingestion pipeline deployment : `cd kubernetes/helm/ingestion-pipeline/arxiv-ingestion-chart`
    - rename `values-sample.yaml` to `values.yaml`
    - update all values to match your deployment.
    You probably only need to update the `hostPath` to point to the folder you will download data into.

* Deploy:
```shell 
microk8s helm install arxiv-ingestion .
```

Check the job are successfully deployed: 
```microk8s kubectl get jobs```


## Test

Once you have some documents to query, you can test the roundtrip is functioning correctly.

```shell
curl -X POST http://localhost:30800/ask -H "Content-Type: application/json" -d '{"query": "tell me about new developments in astronomy."}'
```

## How to debug

Visualize the resources :

```shell
microk8s get <all|resource-type>
```

List deployed charts:

```shell
microk8s helm list
```

it is sometimes useful to bash into existing containers:

```microk8s exec -it ${pod-name} -- bash```
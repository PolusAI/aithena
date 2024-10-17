# Deploy Aithena

After deploying aithena, we need to add some data to our database.
This collection should contains arxiv records with `nomic-embed-text` embeddings.

For that we need either to:
i/ copy an existing collection to our new database.
ii/ deploy the ingestion pipeline that will populate the database with new arxiv records.


### Case 1 - Copy an existing collection

If you have already deployed the stack and have no sudo access, you will need to :

- get qdrant pod :
    `pod_name=$(microk8s kubectl get pods | grep qdrant | awk '{print $1}')`
- copy data to mounted volume:
    `microk8s kubectl cp /path/to/nomic-embed-text-collection/* $(pod-name):/mnt/data/collections/${DOC_DB}`

- kill and restart pod:
    `microk8s kubectl delete $(pod-name)`


### Case 2 - Start the ingestion pipeline
 
 see [arxiv ingestion helm chart](../arxiv-ingestion-job-chart)


## Debug

If there is any issue when deploying,

we need to check that
- qdrant collections are set up.
- ollama models are available.
- aithena services are properly configured.
- aithena agent is properly configured.
- aithena app is properly configured.
- all services are reachable.

Each project README describes ways to do that.
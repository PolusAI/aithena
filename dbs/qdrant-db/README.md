# qdrant

## Setup

Rename `.vars-sample` to `.vars`
Update values according to your deployment.

`source .vars`


## Install

mh install qdrant ./helm  --namespace ${NAMESPACE}
curl http://${HOST}:${NODE_PORT}


### Import data

After deploying the app, we need to add some data.

For that we need either to:
i/ copy an existing collection to our new database.
ii/ copy data from a existing snapshot.
iii/ deploy the ingestion pipeline that will populate the database with new records.


### Case 1 - Copy an existing collection


(If qdrant has been run as priviledged user, you will
need to sudo)

`cp -r collection /path/to/qdrant-data/collections/`

If you have already deployed the stack and have no sudo access, you will need to :

- get qdrant pod :
    `pod_name=$(microk8s kubectl get pods | grep qdrant | awk '{print $1}')`
- copy data to mounted volume:
    `microk8s kubectl cp /path/to/nomic-embed-text-collection/* $(pod-name):/mnt/data/collections/${DOC_DB}`

- kill and restart pod:
    `microk8s kubectl delete $(pod-name)`

### Case 2 - Copy a snaphsot

Download the data snapshots.

### Upload snaphsot to your qdrant db

curl -X POST 'http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${COLLECTION_NAME}/snapshots/upload?priority=snapshot' \
    -H 'Content-Type:multipart/form-data' \
    -F "snapshot=@{ABSTRACTS_SNAPSHOT_PATH}"

curl -X GET 'http://${QDRANT_HOST}:30334/collections/'



### Case 3 - Start the ingestion pipeline
 
 see [arxiv ingestion helm chart](../arxiv-ingestion-job-chart)


### Check we can access the collection.

curl http://${HOST}:${NODE_PORT}/collections
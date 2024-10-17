# qdrant

## Setup

Rename `.vars-sample` to `.vars`
Update values according to your deployment.

`source .vars`


## Install

mh install qdrant ./helm  --namespace ${NAMESPACE}
curl http://${HOST}:${NODE_PORT}


### copy data to qdrant collections.
(If qdrant has been run as priviledged user, you will
need to sudo)

cp -r collection /path/to/qdrant-data/collections/


### Check we can access the collection.

curl http://${HOST}:${NODE_PORT}/collections
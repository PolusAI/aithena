# Ai review app (v0.2.0-dev3)

Ai review is a prototype application that:
- load embeddings from a database
- extract main topics through dimension reduction and clustering
- summarize each cluster of paper chunks / abstracts.
- generate an outline using all generated clusters.

## Pre-requisite

In order to run the documentation commands, rename `.vars-sample` to `.vars`, update and source `.vars`

## Running with docker

```shell
docker run -v /polus2/gerardinad/projects/aithena/.data/:/.app-data  -it --rm --name air --net ${DOCKER_NET} --env-file .env polusai/ai-review-app:0.2.0-dev3
```

Note: if DOCKER_NET != host, you will need to expose the port as well by adding `-p $HOST_PORT:$PORT`

## Data

Download the data snapshots.

### Upload snaphsot to your qdrant db

curl -X POST 'http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${ABSTRACT_DB}/snapshots/upload?priority=snapshot' \
    -H 'Content-Type:multipart/form-data' \
    -F "snapshot=@{ABSTRACTS_SNAPSHOT_PATH}"

 curl -X POST 'http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${PAPERS_DB}/snapshots/upload?priority=snapshot' \
      -H 'Content-Type:multipart/form-data' \
      -F "snapshot=@${PAPERS_SNAPSHOT_PATH}"

curl -X GET 'http://${QDRANT_HOST}:30334/collections/'

## Getting Started

Th goal is to assist a scientist into developing a review paper.

The app revolves around the idea of context, which is a grouping of documents.
Each context can be summarized, label and chat with.
The app also allows you to add notes and new documents.

Contexts can be created manually or automatically extracted via data clustering.

### Processing Tab

Data is extracted from a given collection.
Currently, data must be projected to a 2D space to enable visualization, clustering and summarization.

### Models configuration Tab

All prompts can be configured in this tab.


### Summaries Tab

Currently, outline is only build from cluster summaries.
The 'summarize all' icon after dimension reduction is used to generate those summaries.

### Outline Tab

The outline tab will generate a final outline from all existing clusters.
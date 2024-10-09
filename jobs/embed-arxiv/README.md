# Embed Arxiv (v0.1.0-dev0)

Read arxiv records in arXiv format.
Embed each record abstract
and save the record metadata and the embedding in a qdrant database.

## Tests

### Pre-requisites

Embed arxiv depends on both qdrant vector database and ollama.

Here is a quick way to deployed both with docker:

```shell
docker create network aithena-net
docker run -p 6333:6333 --name qdrant --net aithena-net qdrant/qdrant:latest
docker run -p 11434:11434 --net aithena-net  --name ollama ollama/ollama
```

We will embed using `nomic-embed-text`, make sure it is available.

```shell
docker exec ollama ollama pull nomic-embed-text
```

Lastly, make sure you have downloaded arxiv records to embed.

### Deploy the docker image

Now we can deploy the embed arxiv

```shell
DATA_DIR="~/Documents/projects/ai-review/data/"
RECORDS_DIR="downloads/export.arxiv.org/ListRecords/2024-09-05/arXiv"
docker run -v $DATA_DIR:/inputs --env DB_HOST=qdrant --env EMBED_URL="http://ollama:11434/api/embed"  --name embed-arxiv --net aithena-net  -it polusai/embed-arxiv:0.1.0-dev0-arm64 --inpDir /inputs/$RECORDS_DIR
```

Modify `DATA_DIR` and `RECORDS_DIR` to match your config.

## Examples

`examples` contains example that will run the job as a regular process.

## Automated tests

`pytest tests/test_cli.py` to run as regular process.

Note that all configurations must be done prior to running the tests.

## Note

Previous versions were running local models directly.
Different model requires different versions of the transformer library.
It attempting to run model locally, those are the know compatibilites.

instructor-xl requires transformer 4.25
nvembed requires transformer 4.42

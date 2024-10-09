# OAI-PMH (v0.2.0-dev0)

A client for all oai-pmh services.

## Options

| Name          | Description
|---------------|-------------------------
| `--url`       | service url to pull oaipmh records from. Default to 'https://export.arxiv.org/oai2'.
| `--from`      | retrieve all records from this date. Default to today's date.
| `--format`    | metadata format in wich to retrieve records. Default to 'oai_dc'.
| `--outDir`    | output directory: where to save the downloaded records. Required.

See `src/polus/aithena/oaipmh_client/__main__.py`

## Test Docker Image

Download yesterday's records on arxiv in the arXiv format

```shell
DATE=$(date -v -1d '+%Y-%m-%d') \
OUT_DIR=/path/to/output/directory \
docker run -v $OUT_DIR:/outDir polusai/aithena-oai-pmh-client:0.2.0 --from $DATE --outDir=/outDir --format arXiv
```

## Build docker image

```shell
./build-docker.sh
```

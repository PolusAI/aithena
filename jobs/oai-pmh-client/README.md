# OAI-PMH (v0.2.0-dev0)

A client for all oai-pmh services.




## Test Docker Image

```shell
DATE=$(date -v -1d '+%y-%m-%d') \
OUT_DIR=/path/to/output/directory \
docker run -v $OUT_DIR:/outDir polusai/aithena-oai-pmh-client:0.2.0 --from $DATE --outDir=/outDir
```

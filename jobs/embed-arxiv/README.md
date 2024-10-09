# Embed Arxiv (v0.1.0-dev0)

Read arxiv records in arXiv format.
Embed each record abstract
and save the record metadata and the embedding in a qdrant database.


## Note

Previous versions were running local models directly.
Different model requires different versions of the transformer library.
It attempting to run model locally, those are the know compatibilites.

instructor-xl requires transformer 4.25
nvembed requires transformer 4.42

# Embed openalex

## Install

```python -m venv .venv```
```source .venv/bin/activate```
```poetry install``

## Embed the full database

Provided one have the full import of the database, a full embedding of all abstracts found in db can be done by running :

```nohup .venv/bin/python src/polus/aithena/embed_openalex/embed.py > embed.out 2>&1 &```
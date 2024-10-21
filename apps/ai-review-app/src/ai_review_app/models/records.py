"""Record functions and components for AI Review Dashboard."""

# pylint: disable=W1203, W0106
import re
from typing import Any, Callable

import numpy as np
import pandas as pd
import solara

from qdrant_client.http.models.models import Record

from ..utils.common import get_logger
from . import ContextPart, OldDocument, OldDocumentCollection
from ..components.plot import PointSelection
from ..components.database import db
from .. import config


logger = get_logger(__file__)


def inline_author_names(authors: list) -> str:
    """Return list of authors as a string."""
    ## TODO ellipse long list
    return ", ".join([author["author"][0]["keyname"] for author in authors])


def build_papers_df(metadatas):
    """Build a DataFrame from a list of metadata."""
    data = [
        {"title": m["title"], "authors": inline_author_names(m["authors"])}
        for m in metadatas
        if "title" in m and "authors" in m
    ]
    df = pd.DataFrame(data)
    return df


def get_record_index(records: list[Record], title: str):
    """Return the index of a record with a given title."""
    # TODO: use a better search algorithm
    for i, record in enumerate(records):
        if record.payload["title"][0] == title:
            return i
    return None


def payload_to_context(payload: dict) -> str:
    """Convert a record's payload to a context string for LLM."""
    context = f"<article><title>{payload['title'][0]}</title>"
    context += f"<authors>{inline_author_names(payload['authors'])}</authors>"
    context += f"<abstract>{payload['abstract'][0]}</abstract></article>"
    return context


def record_to_context(record: Record) -> str:
    """Convert a record to a context string for LLM."""
    return payload_to_context(record.payload)


def point_selection_to_context_record(
    point_selection: PointSelection, records: solara.Reactive[list[Record]]
) -> str:  # TODO: import PointSelection
    """Turn a point selection into a context record."""
    return record_to_context(records.value[point_selection.row])


def get_valid_collections(collections: list[str]):
    valid_collections = [
        collection
        for collection in collections
            # if "NV-Embed" in collection
            # or "AAA" in collection
    ]
    return valid_collections


# TODO retrieve a valid collection (filter out bad ones)
def get_valid_collection(collections: list[str]):
    """Return a valid collection from a list of collections."""
    valid_collections = collections
    if len(valid_collections) == 0:
        valid_collections = [None]
        raise Exception("No valid collection found.")
    
    if config.DEFAULT_COLLECTION in valid_collections:
        logger.info(f"return default collection {config.DEFAULT_COLLECTION}")
        return config.DEFAULT_COLLECTION
    
    logger.info(f"return valid collection {valid_collections[0]}")
    return valid_collections[0]


def get_records(collection: str) -> list[Record]:
    """Retrieve records for a given collection."""
    logger.info(f"##### retrieve records for collection {collection}...")
    return db.get_all_records(collection)


# TODO check and rewrite, every data should have vector and payloads
def parse_records(records) -> tuple[np.ndarray, dict[str, Any]]:
    """Parse records into vectors and metadatas."""
    logger.info("parsing records...")
    vectors = np.array([r.vector for r in records if hasattr(r, "vector")])
    metadatas = [r.payload for r in records if hasattr(r, "payload")]
    return vectors, metadatas


def parse_records_as_documents(records: list[Record]) -> list[OldDocument]:
    """Parse records into Document objects."""
    logger.info("parsing records as documents...")
    documents = [OldDocument.from_record(r) for r in records]
    return documents


@solara.component
def DocumentInfo(
    document: OldDocument,
    context_documents_set: set,
    set_context_documents_set: Callable,
):
    """Display the information of a record."""

    def get_in_context():
        logger.info(f"checking if {document.title} is in context...")
        logger.info(f"current context: {context_documents_set}")
        logger.info(ContextPart(content=document) in context_documents_set)
        return ContextPart(content=document) in context_documents_set

    in_context = get_in_context()

    def modify_context_list(val):
        new_context_documents = context_documents_set.copy()
        if val is False:
            if ContextPart(content=document) in context_documents_set:
                logger.info("removing document from context...")
                new_context_documents.remove(ContextPart(content=document))
                set_context_documents_set(new_context_documents)
        if val is True:
            if ContextPart(content=document) not in context_documents_set:
                logger.info("adding document to context...")
                new_context_documents.add(ContextPart(content=document))
                set_context_documents_set(new_context_documents)
            else:
                return

    with solara.Column(style={"padding-left": "10px"}, gap="6px") as main:
        with solara.Row(gap="0px", style={"position": "relative"}):
            solara.Markdown(f"# {document.title}"),
            with solara.Div(style={"position": "relative", "padding": "11px"}):
                solara.Checkbox(
                    label="Context",
                    value=in_context,
                    on_value=modify_context_list,
                )
        solara.Markdown(f"## {document.authors_str}"),
        solara.Markdown(f"{document.abstract}"),
    return main

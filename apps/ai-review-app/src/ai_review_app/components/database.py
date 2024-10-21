"""Database service and related solara components."""
# pylint: disable=C0103, W0106, C0116, W1203, R0913, R0914, R0915, W0613
# TODO review DB integration, especially exception thrown by Qdrant, maybe wrap around generic DB exceptions.
# DB exceptions are not recoverable unless we let the user define the DB connection.
# so they should inherit from a base unrecoverable exception that displays a `contact admin` message.
from typing import Callable

from ai_review_app.models.context import Document, SimilarDocument
from ai_review_app.services.document_factory import convert_record_to_doc, convert_records_to_docs
import numpy as np
import solara

from polus.aithena.common.utils import batcher
from polus.aithena.document_services.arxiv_abstract_ingestion.db.qdrant_db import ArxivQdrantClient

from ..utils.common import get_logger
import ai_review_app.config as config
from solara.lab import task
from qdrant_client.http.models.models import Record

logger = get_logger(__file__)

class InvalidQdrantConnectionError(Exception):
    """Exception raised when connection to Qdrant is invalid."""


class NoCollectionsFoundError(Exception):
    """Exception raised when no collections are found in Qdrant."""

try:
    logger.debug(f"attempting to connect to local qdrant instance on port {config.QDRANT_PORT}...")
    db = ArxivQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
except Exception as e:
    raise InvalidQdrantConnectionError(f"Cannot connect to Qdrant: {e}") from e

try:
    COLLECTIONS = db.list_collections()
except Exception as e:
    # TODO improve exception, other types error can be raised.
    COLLECTIONS = []
    raise NoCollectionsFoundError(f"No collections found in Qdrant: {e}") from e

if len(COLLECTIONS) == 0:
    raise NoCollectionsFoundError(
        "No collections found, check your connection to Qdrant."
    )

def query_db(embedding_service, collection_: str, query_: str) -> list[Record]:
    """Embed a query and use it to query the database."""
    logger.info(f"collection {collection_} query: {query_}")
    embedding_requests = [[config.QUERY_DB_INSTRUCTION, query_]]
    query_embeddings = []
    for batch in batcher(embedding_requests, 1):
        query_embeddings = embedding_service.embed_all(batch, 1)
    if len(query_embeddings) == 0:
        raise Exception("Embedding failed!")
    encoded_query = query_embeddings[0].numpy()
    # encoded_query= np.array(query_embeddings[0])
    logger.debug(encoded_query)
    res = db.client.query_points(collection_, encoded_query)
    return res

@solara.component
def SelectCollections(
    collections_: list[str], collection_: str, set_collection_: Callable
):
    """Select Collection."""
    solara.Select(
        label="collection",
        values=collections_,
        value=collection_,
        on_value=set_collection_,
    )
    solara.Markdown(f"Selected collection: {collection_}")


@solara.component
def CollectionInfo(collection_, records_, vectors_):
    """Display collection details."""
    with solara.Column():
        solara.Markdown(f"Collection :  {collection_}")
        solara.Markdown(f"Records count :  {len(records_)}")
        solara.Markdown(f"Embeddings dimensionality :  {vectors_.shape[1]}")


@solara.component
def SearchBox(
    embedding_service,
    collection_,
    query_responses : solara.Reactive[dict[str,SimilarDocument]]
    ):

    # TODO turn to async task
    def run_similarity_query(query_string):
        resp = query_db(embedding_service, collection_, query_string)
        records = [Record(id=point.id, payload=point.payload, vector=point.vector) for point in resp.points]
        docs = convert_records_to_docs(records)
        similar_docs = [SimilarDocument(document=doc, score=point.score) for doc, point in zip(docs, resp.points)]
        query_responses.value = {doc.document.id: doc for doc in similar_docs}

    query_ = solara.use_reactive("")
    solara.InputText(
        label="Type query.", value=query_.value, on_value=run_similarity_query
    )

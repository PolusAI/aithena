from polus.aithena.common.logger import get_logger
from polus.aithena.document_services.arxiv_abstract_ingestion import (
    arxiv_types as arxiv,
)
from polus.aithena.document_services.arxiv_abstract_ingestion.db.qdrant_db import (
    ArxivQdrantClient,
)
from pydantic import BaseModel
from qdrant_client import models

logger = get_logger(__file__)


def register_arxiv_metadata_with_instructorXL_embeddings(
    db: ArxivQdrantClient, source_id
):
    schema = arxiv.ArXiv.model_json_schema()
    vector_size = 768
    distance = models.Distance.COSINE
    vector_config = models.VectorParams(size=vector_size, distance=distance)
    embedding_model = "hkunlp/instructor-xl"
    try:
        db.register_collection(
            source_id,
            schema,
            vector_config=vector_config,
            embedding_model=embedding_model,
        )
    except ValueError:
        logger.debug(f"source already registered {source_id}")


def register_arxiv_metadata_with_nvembed_embeddings(db: ArxivQdrantClient, source_id):
    schema = arxiv.ArXiv.model_json_schema()
    vector_size = 4096
    distance = models.Distance.COSINE
    vector_config = models.VectorParams(size=vector_size, distance=distance)
    embedding_model = "nvidia/NV-Embed-v1"
    try:
        db.register_collection(
            source_id,
            schema,
            vector_config=vector_config,
            embedding_model=embedding_model,
        )
    except ValueError:
        logger.debug(f"source already registered {source_id}")


def register_arxiv_metadata_with_nomic768_embeddings(db: ArxivQdrantClient, source_id):
    schema = arxiv.ArXiv.model_json_schema()
    vector_size = 768
    distance = models.Distance.COSINE
    vector_config = models.VectorParams(size=vector_size, distance=distance)
    embedding_model = "nomic-embed-text"
    try:
        db.register_collection(
            source_id,
            schema,
            vector_config=vector_config,
            embedding_model=embedding_model,
        )
    except ValueError:
        logger.debug(f"source already registered {source_id}")


class MultiVectorConfig(BaseModel):
    vectors_config: dict[str, models.VectorParams]

"""Embed all arxiv metadadata for a given a date.

The date must correspond to a downloaded set of records store on disk.
"""
import datetime
from pathlib import Path
import time

from polus.aithena.common.logger import get_logger
from polus.aithena.document_services.arxiv_abstract_ingestion import config
from polus.aithena.document_services.arxiv_abstract_ingestion.arxiv_ingest import (
    ArxivIngester,
)
from polus.aithena.document_services.arxiv_abstract_ingestion.db import qdrant_db_tasks
from polus.aithena.document_services.arxiv_abstract_ingestion.db.qdrant_db import (
    ArxivQdrantClient,
)
from polus.aithena.document_services.arxiv_abstract_ingestion.embed.embed_nvembed import (
    EmbedderNvEmbed,
)

logger = get_logger(__file__)


def embed_abstracts_nvembed(
    inp_dir: Path | None = None, date: datetime.datetime | None = None
) -> None:
    db = ArxivQdrantClient(host=config.DB_HOST, port=config.DB_PORT)
    source_id = config.DB_ABSTRACT_COLLECTION
    qdrant_db_tasks.register_arxiv_metadata_with_nvembed_embeddings(db, source_id)

    # TODO remove that
    ingester = ArxivIngester(config.ARXIV_LIST_RECORDS_DIR, config.ARXIV_INGEST_LOG_DIR)

    start = time.perf_counter()
    if inp_dir is not None:
        inp_dir = inp_dir.resolve()
        if not inp_dir.exists():
            raise FileNotFoundError(f"Directory does not exist: {inp_dir}")
        logger.debug(f"start embedding data from: {inp_dir}")
        total_count = ingester.embed_arxiv_records_dir(
            inp_dir=inp_dir,
            db=db,
            collection_name=source_id,
            embedder=EmbedderNvEmbed(config.MAX_WORKERS),
            embed_instruction=config.EMBED_INSTRUCTION,
            batch_size=config.BATCH_SIZE,
            embed_model_batch_size=config.EMBED_MODEL_BATCH_SIZE,
            update=True,
        )
    elif date is not None:
        # TODO extract date utilities and revert to inp_dir case
        logger.debug(f"start embedding data for date: {date}")
        total_count = ingester.embed_arxiv_records_date(
            date=date,
            db=db,
            collection_name=source_id,
            embedder=EmbedderNvEmbed(config.MAX_WORKERS),
            embed_instruction=config.EMBED_INSTRUCTION,
            batch_size=config.BATCH_SIZE,
            embed_model_batch_size=config.EMBED_MODEL_BATCH_SIZE,
            update=True,
        )
    else:
        raise ValueError("Either inp_dir or date must be provided.")

    end = time.perf_counter()
    wall_time = round(end - start)

    logger.info(
        f"""params:
                DB:{db.node_url}
                COLLECTION_NAME={source_id}
                EMBED_INSTRUCTION={config.EMBED_INSTRUCTION}
                BATCH_SIZE={config.BATCH_SIZE}
                EMBED_MODEL_BATCH_SIZE={config.EMBED_MODEL_BATCH_SIZE}
    """,
    )
    logger.info(f"embedded and saved: {total_count} records.")
    logger.info(f"wall time: {datetime.timedelta(seconds=wall_time)}")

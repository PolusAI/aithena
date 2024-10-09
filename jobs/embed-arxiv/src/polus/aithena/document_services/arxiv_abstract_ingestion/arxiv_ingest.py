"""Ingest new records."""
import datetime
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import batcher
from polus.aithena.common.utils import init_dir
from polus.aithena.document_services.arxiv_abstract_ingestion import (
    arxiv_types as arxiv,
)
from polus.aithena.document_services.arxiv_abstract_ingestion import config
from polus.aithena.document_services.arxiv_abstract_ingestion.db.qdrant_db import (
    ArxivQdrantClient,
)
from polus.aithena.document_services.arxiv_abstract_ingestion.embed.embed import (
    Embedder,
)
from polus.aithena.oaipmh_client import oai_pmh_types as oai
from xsdata_pydantic.bindings import XmlParser

logger = get_logger(__file__)


class ArxivIngestionError(Exception):
    """Arxiv Ingestion Error."""


class ArxivIngester:
    """Manage Ingestion of Arxiv Data."""

    def __init__(
        self,
        arxiv_response_dir: Path = config.ARXIV_LIST_RECORDS_DIR,
        log_dir: Path = config.LOG_DIR,
    ) -> None:
        """Init Arxiv Ingester.

        Args:
         arxiv_response_dir: where to store the server response.
         log_dir: where to write logs.
        """
        if not arxiv_response_dir.exists() or not arxiv_response_dir.is_dir():
            msg = (
                f"{arxiv_response_dir.as_posix()} must exists and must be a directory."
            )
            raise OSError(
                msg,
            )
        self.arxiv_response_dir = arxiv_response_dir
        self.log_dir = log_dir
        self.parse_metadatas_error_log_file = log_dir / "parse_err.log"
        self.xml_parser = XmlParser()

    def _get_dir(self, date: datetime.datetime, metadata_prefix="arXiv"):
        """Select a record directory containing records for a given pull date."""
        year_month_day_format = "%Y-%m-%d"
        date = date.strftime(year_month_day_format)
        return self.arxiv_response_dir / str(date) / metadata_prefix

    def iter_records(
        self,
        date: datetime.datetime,
        metadata_schema: str = "arXiv",
    ) -> Iterator[tuple[list[arxiv.ArXivType], Path]]:
        """Iterate through a record directory in batch.

        Ignore records marked as deleted.
        Ignore files that cannot be processed but log them in an error log file.

        Returns:
          Metadata for each record file at a given pull date.
        """
        # currently only support arxiv metadata format.
        if metadata_schema != "arXiv":
            msg = f"the metadata schema: {metadata_schema} is not supported."
            raise NotImplementedError(msg)

        source_dir = self._get_dir(date, metadata_schema)
        for file in source_dir.iterdir():
            try:
                if file.suffix != ".xml":
                    logger.debug(f"ignoring non-xml file : {file}...")
                logger.debug(f"processing file {file}...")
                arxiv_metadatas = self.parse_arxiv_records_file(file)
            except ArxivIngestionError as e:
                logger.exception(exc_info=e)
                with self.parse_metadatas_error_log_file.open("a+") as f:
                    f.writelines([f"{file} \n"])
                continue
            yield arxiv_metadatas, file

    def iter_records_dir(
        self,
        inp_dir: Path,
        metadata_schema: str = "arXiv",
    ) -> Iterator[tuple[list[arxiv.ArXivType], Path]]:
        """Iterate through a record directory in batch.

        Ignore records marked as deleted.
        Ignore files that cannot be processed but log them in an error log file.

        Returns:
          Metadata for each record file at a given pull date.
        """
        # currently only support arxiv metadata format.
        if metadata_schema != "arXiv":
            msg = f"the metadata schema: {metadata_schema} is not supported."
            raise NotImplementedError(msg)

        for file in inp_dir.iterdir():
            try:
                if file.suffix != ".xml":
                    logger.debug(f"ignoring non-xml file : {file}...")
                logger.debug(f"processing file {file}...")
                arxiv_metadatas = self.parse_arxiv_records_file(file)
            except ArxivIngestionError as e:
                logger.exception(exc_info=e)
                with self.parse_metadatas_error_log_file.open("a+") as f:
                    f.writelines([f"{file} \n"])
                continue
            yield arxiv_metadatas, file

    def parse_arxiv_records_file(self, file: Path):
        """Parse arxiv records with metadata in arxiv format.

        Note that records marked as DELETED will be ignored.

        Returns:
            The list of arxiv metadata contained in the provided file.

        Raises:
             ArxivIngestionError if an error has occured.
        """
        try:
            records = self.xml_parser.parse(file, oai.OaiPmhtype).list_records.record

            arxiv_metadatas = [
                arxiv.ArXivType(**record.metadata.other_element.model_dump())
                for record in records
                if record.header.status != oai.StatusType.DELETED
            ]
        except Exception as e:
            msg = f"Unable to parse arxiv record file: {file}"
            raise ArxivIngestionError(msg) from e
        return arxiv_metadatas

    def embed_arxiv_records_date(
        self,
        date: datetime.datetime,
        db: ArxivQdrantClient,
        collection_name: str,
        embedder: Embedder,
        embed_instruction: str,
        batch_size: int,
        embed_model_batch_size: int,
        update: bool = False,
    ):
        """Embed arxiv abstracts and save to db.

        Args:
            db: the db where to store embeddings.
            update: True to overwrite existing records,
                    False will skip re-embedding if record already exists.
        """
        total_insert_count = (
            0  # count how many new records are embedded and inserted in the db
        )

        LOG_DIR = init_dir(self.log_dir / date.strftime(config.DATE_FORMAT))
        LOG_FILE = LOG_DIR / f"embed_err_{date.strftime(config.DATE_FORMAT)}.txt"

        with embedder:
            for records, file in self.iter_records(date):
                ids_ = [db.create_hash(record.id[0]) for record in records]
                working_set = list(zip(ids_, records))

                # if no update, first filter out records that already exist
                if not update:
                    db_records = db.client.retrieve(
                        collection_name=collection_name,
                        ids=ids_,
                        with_payload=False,
                        with_vectors=False,
                    )
                    existing_ids = {record.id for record in db_records}
                    working_set = [
                        item for item in working_set if item[0] not in existing_ids
                    ]
                    ids_ = [record[0] for record in working_set]

                if len(ids_) == 0:
                    logger.debug("all documents in record file have been processed.")
                    continue

                abstracts = [
                    [embed_instruction, record[1].abstract[0]] for record in working_set
                ]

                # embed all docs in batch and insert each new batch to the db.
                batch_index = 0
                for batch in batcher(abstracts, batch_size):
                    batch_start_index = batch_index * batch_size
                    batch_ids = []
                    batch_payloads = []
                    batch_embeddings = []
                    embeddings = embedder.embed_all(batch, embed_model_batch_size)
                    for index, embedding in enumerate(embeddings):
                        record = working_set[batch_start_index + index][1]
                        record_id = record.id[0]
                        if embedding is not None:
                            logger.debug(f"paper embedded : {record_id}")
                            batch_ids.append(ids_[batch_start_index + index])
                            batch_payloads.append(record.model_dump())
                            batch_embeddings.append(embedding)
                        else:
                            logger.error(
                                f"could not embed abstract of paper : {record_id}",
                            )
                            with LOG_FILE.open("a+") as f:
                                f.writelines([f"{file.name} {record_id} \n"])

                    if len(batch_ids) != 0:
                        db.upsert(
                            collection_name,
                            batch_ids,
                            batch_payloads,
                            batch_embeddings,
                        )
                        total_insert_count += len(batch_ids)
                    batch_index += 1

        return total_insert_count

    def embed_arxiv_records_dir(
        self,
        inp_dir: Path,
        db: ArxivQdrantClient,
        collection_name: str,
        embedder: Embedder,
        embed_instruction: str,
        batch_size: int,
        embed_model_batch_size: int,
        max_workers: Optional[int] = None,
        update: bool = False,
    ):
        """Embed arxiv abstracts and save to db.

        Args:
            db: the db where to store embeddings.
            update: True to overwrite existing records,
                    False will skip re-embedding if record already exists.
        """
        total_insert_count = (
            0  # count how many new records are embedded and inserted in the db
        )

        date = datetime.datetime.now()

        LOG_DIR = init_dir(self.log_dir / date.strftime(config.DATE_FORMAT))
        LOG_FILE = LOG_DIR / f"embed_err_{date.strftime(config.DATE_FORMAT)}.txt"

        with embedder:
            for records, file in self.iter_records_dir(inp_dir):
                ids_ = [db.create_hash(record.id[0]) for record in records]
                working_set = list(zip(ids_, records))

                # if no update, first filter out records that already exist
                if not update:
                    db_records = db.client.retrieve(
                        collection_name=collection_name,
                        ids=ids_,
                        with_payload=False,
                        with_vectors=False,
                    )
                    existing_ids = {record.id for record in db_records}
                    working_set = [
                        item for item in working_set if item[0] not in existing_ids
                    ]
                    ids_ = [record[0] for record in working_set]

                if len(ids_) == 0:
                    logger.debug("all documents in record file have been processed.")
                    continue

                abstracts = [
                    [embed_instruction, record[1].abstract[0]] for record in working_set
                ]

                # embed all docs in batch and insert each new batch to the db.
                batch_index = 0
                for batch in batcher(abstracts, batch_size):
                    batch_start_index = batch_index * batch_size
                    batch_ids = []
                    batch_payloads = []
                    batch_embeddings = []
                    embeddings = embedder.embed_all(batch, embed_model_batch_size)
                    for index, embedding in enumerate(embeddings):
                        record = working_set[batch_start_index + index][1]
                        record_id = record.id[0]
                        if embedding is not None:
                            logger.debug(f"paper embedded : {record_id}")
                            batch_ids.append(ids_[batch_start_index + index])
                            batch_payloads.append(record.model_dump())
                            batch_embeddings.append(embedding)
                        else:
                            logger.error(
                                f"could not embed abstract of paper : {record_id}",
                            )
                            with LOG_FILE.open("a+") as f:
                                f.writelines([f"{file.name} {record_id} \n"])

                    if len(batch_ids) != 0:
                        db.upsert(
                            collection_name,
                            batch_ids,
                            batch_payloads,
                            batch_embeddings,
                        )
                        total_insert_count += len(batch_ids)
                    batch_index += 1

        return total_insert_count

    def get_arxiv_pull_date(self, date: datetime.datetime):
        """Return pull date for a given record directory."""
        dir = self._get_dir(date)
        earliest_creation_time = datetime.datetime.now()
        for file in dir.iterdir():
            timestamp = file.stat().st_ctime
            creation_time = datetime.datetime.fromtimestamp(timestamp)
            if creation_time < earliest_creation_time:
                earliest_creation_time = creation_time
        return creation_time.strftime("%Y-%m-%d")

    def get_arxiv_latest_paper_date(self, date: datetime.datetime):
        """Return the date of the latest paper contained in a record directory."""
        latest_paper_date = datetime.datetime(1970, 1, 1)
        for records, _ in self.iter_records(date):
            for record in records:
                paper_date_string = record.created[0]
                paper_date = datetime.datetime.strptime(paper_date_string, "%Y-%m-%d")
                if paper_date > latest_paper_date:
                    latest_paper_date = paper_date
        return latest_paper_date.strftime("%Y-%m-%d")

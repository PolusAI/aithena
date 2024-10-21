import hashlib
import os
import uuid
from pathlib import Path
from typing import Any
from typing import Optional
from typing import Union

import requests
from polus.aithena.common.logger import get_logger
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import Batch
from qdrant_client.models import Distance
from qdrant_client.models import PointStruct
from qdrant_client.models import VectorParams

logger = get_logger(__file__)


class ArxivQdrantClient:
    """A client that simplifies interaction with the Qdrant database."""

    def __init__(self, host: str = "localhost", port: int = 6333) -> None:
        self.node_url = f"{host}:{port}"
        logger.debug(f"connecting to qdrant on host {host} and port {port}")
        self.client = QdrantClient(host=host, port=port, timeout=100)
        self.schemas_collection_name = "schemas"
        if not self.client.collection_exists(self.schemas_collection_name):
            logger.debug(f"creating schemas collection {self.schemas_collection_name}")
            self.client.create_collection(
                self.schemas_collection_name,
                VectorParams(size=1, distance=Distance.COSINE),
            )

    def create_collection(self, col_name: str, vector_size: int) -> bool:
        """Create a new collection with given name and vector size.

        Args:
            - col_name: the name of the collection
            - vector_size: the size of the embedding vector
        """
        return self.client.create_collection(
            collection_name=col_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def collection_exists(self, name: str):
        """Check if a collection exists.

        Args:
            - name: the name of the collection
        """
        return self.client.collection_exists(name)

    def delete_collection(self, name: str):
        """Delete a collection.

        Args:
            - name: the name of the collection
        """
        self.client.delete_collection(collection_name=name)
        id_ = self.create_hash(name)
        self.client.delete(
            collection_name=self.schemas_collection_name,
            points_selector=models.PointIdsList(
                points=[id_],
            ),
        )

    def upsert(
        self,
        collection: str,
        ids_: list[int],
        payloads: list[BaseModel],
        vectors: list[Any],
    ):
        """Update or insert a new point into the collection.

        If point with given ID already exists - it will be overwritten.
        """
        return self.client.upsert(
            collection_name=collection,
            points=Batch(
                ids=ids_,
                payloads=payloads,
                vectors=vectors,
            ),
        )

    def register_collection(
        self,
        collection_name: str,
        json_schema,
        vector_config: VectorParams,
        embedding_model: str,
        params: Optional[dict] = None,
        exist_ok: bool = True,
    ) -> None:
        """Register a new source in the database.

        Args:
            - collection_name: the name of the collection
            - json_schema: the json schema of the collection,
            - vector_config: the vector configuration of the collection,
            - embedding_model: the embedding model used to create the vectors,
            - params: additional parameters,
            - exist_ok: if True, do not raise an exception if the
                collection already exists.
        """
        id_ = self.create_hash(collection_name)
        schema_exist = self.client.retrieve(
            collection_name=self.schemas_collection_name,
            ids=[id_],
        )
        collection_exist = self.client.collection_exists(
            collection_name=collection_name,
        )

        if schema_exist and collection_exist:
            msg = f"source already exists : {collection_name}"
            if exist_ok:
                logger.warning(msg)
                return
            else:
                raise Exception(msg)

        # register this new schema
        logger.debug(f"register new schema: {collection_name}")
        self.client.upsert(
            collection_name=self.schemas_collection_name,
            points=[
                PointStruct(
                    id=id_,
                    payload={
                        "source_id": collection_name,
                        "json_schema": json_schema,
                        "vector_config": vector_config.model_dump(),
                        "embedding_model": embedding_model,
                        "params": params,
                    },
                    vector=[1],
                ),
            ],
        )
        logger.debug(f"create new collection: {collection_name}")
        self.client.create_collection(collection_name, vectors_config=vector_config)

    def create_hash(self, id_: str) -> str:
        """Create a unique uuid from a unique string."""
        hash_obj = hashlib.sha256(id_.encode("utf-8"))
        hex_hash = hash_obj.hexdigest()
        uuid_ = uuid.UUID(hex_hash[:32])
        return str(uuid_)

    def create_snapshot(self, collection_name, snapshots_path: Path):
        snapshot_info = self.client.create_snapshot(
            collection_name=collection_name
        )  # noqa
        snapshot_url = f"{self.node_url}/collections/{collection_name}/snapshots/{snapshot_info.name}"  # noqa
        local_snapshot_path = os.path.join(snapshots_path, snapshot_info.name)

        response = requests.get(snapshot_url)
        with open(local_snapshot_path, "wb") as f:
            response.raise_for_status()
            f.write(response.content)

        return snapshot_info

    def upload_snapshot(self, snapshot_file: Path, collection_name: str):
        snapshot_name = snapshot_file.name
        requests.post(
            f"{self.node_url}/collections/{collection_name}/snapshots/upload?priority=snapshot",
            files={"snapshot": (snapshot_name, open(snapshot_file, "rb"))},
        )

    def get_records(self, collection_name, key, value, limit=5):
        return self.client.scroll(
            limit=limit,
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    ),
                ],
            ),
        )

    def get_all_records(
        self,
        collection_name: str,
        with_payload=True,
        with_vectors=True,
        limit: Optional[int] = None,
        batch_size: int = 1000,
    ) -> list[Any]:
        """Get all records in a given collection.

        Return:
            The list of all records.
        """
        limit_ = limit if limit is not None and limit < batch_size else batch_size

        offset = 0
        records = []
        while offset is not None:
            if limit is not None and len(records) >= limit:
                break
            page_rec = self.client.scroll(
                collection_name=collection_name,
                limit=limit_,
                offset=offset,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )
            offset = page_rec[1]
            records += page_rec[0]

        if limit is not None and len(records) > limit:
            records = records[:limit]

        logger.debug(f"retrieved {len(records)} records")
        return records

    def list_collections(self, filter_size: Union[int, None] = None):
        """Return all existing collections.

        Args:
            - filter_size: filter the collection by embedding size
        """
        resp = self.client.get_collections()
        cols = resp.collections
        cols = [col.name for col in cols if col.name != "schemas"]

        if filter_size is None:
            return cols

        valid_cols = []
        schemas = [col.name for col in cols if col.name == "schemas"][0]
        if not schemas:
            msg = "no schemas collection found!"
            raise Exception(msg)
        for col in cols:
            try:
                schema = self.get_records(schemas, "source_id", col)[0][0]
                size = schema.payload["vector_config"]["size"]
                if size == 4096:
                    valid_cols.append(col)
            finally:
                continue
        return valid_cols

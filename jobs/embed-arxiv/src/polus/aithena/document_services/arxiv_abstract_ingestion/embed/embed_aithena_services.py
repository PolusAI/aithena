"""Embedder nvembed implementation."""

import json
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from threading import current_thread

import numpy as np
from polus.aithena.common.logger import get_logger
from polus.aithena.document_services.arxiv_abstract_ingestion import config
from polus.aithena.document_services.arxiv_abstract_ingestion.embed.embed import (
    Embedder,
)
from polus.aithena.document_services.arxiv_abstract_ingestion.embed.embed import (
    EmbeddingResult,
)
import requests

logger = get_logger(__file__)


class EmbedderAithenaServices(Embedder):
    """Embedder.

    Embed a list of documents according to instructions.
    Embedding processes are dispatched on several devices as requested.
    """

    def __init__(self, max_workers: int) -> None:
        """Embedder."""
        q = (
            multiprocessing.Queue()
        )  # used to associate a model instance to a specific device.
        for worker in range(max_workers):
            q.put(worker)

        # each worker is associated with one model.
        logger.debug(f"settings up {max_workers} workers...")

        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            initializer=self.create_embedder,
            initargs=(q,),
        )

    def create_embedder(model, queue: multiprocessing.Queue):
        """Load model on an available gpu."""
        device = queue.get()
        logger.debug(f"initialize converter on device {device}")
        thread = current_thread()
        thread.device = device

    def __enter__(self):
        logger.debug("context manager starts.")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.executor.shutdown(wait=True)
        logger.debug("context manager stops : executor shutdown")

    # def embed_request(self, str):
    #     url = "http://10.152.183.102:80/embed/nomic-embed-text/generate"
    #     payload = {"text": "this is a test embedding"}
    #     headers = {"Content-Type": "application/json"}

    #     response = requests.post(url, data=json.dumps(payload), headers=headers)
    #     response.raise_for_status()  # Raise an error for bad status codes
    #     result = response.json()
    #     return result

    def embed_request(self, doc):
        url = config.EMBED_URL
        payload = {"model": "nomic-embed-text", "input": doc}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        result = response.json()["embeddings"]
        print(result)
        return result

    def embed_task(self, docs: list[list[str, str]], task_index):
        """Embed some a batch of documents."""
        thread = current_thread()
        logger.debug(
            f"running embedding {task_index} on thread {thread}, device {thread.device}..."
        )
        docs = [doc[1] for doc in docs]  # remove instruction
        embeddings = self.embed_request(docs)
        embeddings_array = np.array(embeddings)

        return EmbeddingResult(embeddings_array, thread.device)

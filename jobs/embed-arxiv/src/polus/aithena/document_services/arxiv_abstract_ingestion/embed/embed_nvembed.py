"""Embedder nvembed implementation."""

import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from threading import current_thread

from polus.aithena.common.logger import get_logger
from polus.aithena.document_services.arxiv_abstract_ingestion.embed.embed import (
    Embedder,
)
from polus.aithena.document_services.arxiv_abstract_ingestion.embed.embed import (
    EmbeddingResult,
)
from transformers import AutoModel

logger = get_logger(__file__)


class EmbedderNvEmbed(Embedder):
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

    def create_embedder(self, queue: multiprocessing.Queue):
        """Load model on an available device."""
        device = queue.get()
        logger.debug(f"initialize converter on device {device}")
        thread = current_thread()
        thread.device = device
        # model = AutoModel.from_pretrained("nvidia/NV-Embed-v1", trust_remote_code=True)
        model = AutoModel.from_pretrained(
            "nvidia/NV-Embed-v1", local_files_only=True, trust_remote_code=True
        )
        # DOES NOT WORK
        # model = AutoModel.from_pretrained("/Users/antoinegerardin/.cache/huggingface/hub/models--nvidia--NV-Embed-v1", local_files_only=True, trust_remote_code=True)
        thread.embedder = model

    def __enter__(self):
        logger.debug("context manager starts.")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.executor.shutdown(wait=True)
        logger.debug("context manager stops : executor shutdown")

    def embed_task(self, docs: list[list[str, str]], task_index):
        """Embed some a batch of documents."""
        thread = current_thread()
        logger.debug(f"running embedding {task_index} on device {thread.device}...")
        max_length = 4096
        query_prefix = f"Instruct: {docs[0][0]} \nQuery: "
        docs = [doc[1] for doc in docs]  # remove instruction
        embeddings = thread.embedder.encode(
            docs,
            instruction=query_prefix,
            max_length=max_length,
        )
        return EmbeddingResult(embeddings, thread.device)

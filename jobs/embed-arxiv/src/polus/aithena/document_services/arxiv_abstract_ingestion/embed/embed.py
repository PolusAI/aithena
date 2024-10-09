"""Generic embedder API."""

from collections.abc import Iterable
from concurrent.futures import as_completed
from dataclasses import dataclass
from typing import Optional

import numpy as np
from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import batcher

logger = get_logger(__file__)


@dataclass
class EmbeddingResult:
    """Embedding Result."""

    embeddings: np.ndarray
    device_id: int


class Embedder:
    """Embedder.

    Embed a list of documents according to instructions.
    Embedding processes are dispatched on several gpus as requested.
    """

    def __enter__(self):
        logger.debug("context manager starts.")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.executor.shutdown(wait=True)
        logger.debug("context manager stops : executor shutdown")

    def embed(self, docs: Iterable[list[str, str]], batch_size: Optional[int] = None):
        """Embed all docs in batches.

        Args:
            docs: list of [instruction, text]
            batch_size: number of embeddings to process per model.
        """
        batch_size = batch_size if batch_size is not None else 1
        logger.debug(f"embedding docs in batches of size : {batch_size}.")

        failures = []
        successes = []
        futures = {}
        batch_index = 0

        for batch in batcher(docs, batch_size):
            futures[
                self.executor.submit(self.embed_task, batch, batch_index)
            ] = batch_index
            batch_index += 1

        for future in as_completed(futures):
            batch_index = futures[future]
            exception = future.exception()
            if exception:
                logger.error(exception)
                failures.append((batch_index, exception))
            else:
                res = future.result()
                logger.debug(
                    f"batch {batch_index} of size {res.embeddings.shape[0]} - conversion on gpu {res.device_id} completed.",
                )
                successes.append((batch_index, res.embeddings))
        return successes, failures

    def embed_all(
        self, docs: Iterable[tuple[str, str]], batch_size: Optional[int] = None
    ):
        """Embed all docs.
        Embed all docs and returns a list of embeddings of same size as inputs
        and in the same order.
        If an embedding has failed, the element will be None.

        Args:
            docs: list of tuple of (Instruction, Text)
            batch_size: number of embeddings to process per model call.

        """
        successes, _ = self.embed(docs, batch_size)
        embeddings: list[np.ndarray] = [None] * len(docs)

        for batch_index, vector in successes:
            if vector.ndim == 1:
                embeddings[batch_index * batch_size] = vector
            else:
                for i in range(vector.shape[0]):
                    embeddings[batch_index * batch_size + i] = vector[i, :]
        return embeddings

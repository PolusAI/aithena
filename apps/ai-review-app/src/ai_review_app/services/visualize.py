from typing import Any, Literal
import logging
from dotenv import load_dotenv, find_dotenv
import os
from pathlib import Path
import time
import numpy as np
from pydantic import BaseModel
import umap
import hdbscan


load_dotenv(find_dotenv())
data_path = Path(os.environ.get("DATA_PATH",""))

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DistanceMetrics = Literal[
    "euclidean",
    "manhattan",
    "chebyshev",
    "minkowski",
    "canberra",
    "braycurtis",
    "mahalanobis",
    "wminkowski",
    "seuclidean",
    "cosine",
    "correlation",
    "hamming",
    "jaccard",
    "dice",
    "russelrao",
    "kulinski",
    "ll_dirichlet",
    "hellinger",
    "rogerstanimoto",
    "sokalmichener",
    "sokalsneath",
    "yule",
]

class UmapParams(BaseModel):
    n_neighbors: int
    min_dist: float
    n_components: int
    metric: DistanceMetrics


def reduce(vectors: np.ndarray, options: dict[str, Any]):
    """Run UMAP dimension reduction on the array of vectors.

    For possible options, see :
    https://umap-learn.readthedocs.io/en/latest/api.html
    """
    start = time.perf_counter()
    reduced_embeddings = umap.UMAP(
        **options
    ).fit_transform(vectors)
    end = time.perf_counter()
    logger.debug(f"{end - start} seconds to reduce dataset dims...")

    return reduced_embeddings


class HdbscanParams(BaseModel):
    min_samples: int
    min_cluster_size: int
    max_cluster_size: int


def cluster(vectors: np.ndarray, options: dict[str, Any]):
    """Run HDBScan clustering on the array of vectors.

    For possible options, see :
    https://hdbscan.readthedocs.io/en/latest/api.html
    """    
    clusterer = hdbscan.HDBSCAN(**options)
    results = clusterer.fit_predict(vectors)

    # Filter data not associated to a cluster
    labeled = (results >= 0)
    logger.debug(f"number of classified embeddings : {labeled.sum()}/{vectors.shape[0]}")
    return results
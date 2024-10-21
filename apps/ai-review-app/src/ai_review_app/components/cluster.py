"""Clustering Algorithms and Components."""

# pylint: disable=C0103, W0106, C0116, W1203, R0913, R0914, R0915, W0613

from functools import partial

from ai_review_app.models.context import Document
import solara
from ai_review_app.utils.common import get_logger
from ai_review_app.components.database import db
from solara.lab import task
from ai_review_app.services.visualize import HdbscanParams, cluster

logger = get_logger(__file__)


def knn_search(vector, collection_name):
    res = db.client.query_points(
        collection_name=collection_name,
        query=vector,
        with_payload=True,
        with_vectors=True
    )
    return res


@task
async def run_hdbscan(embeddings_, embeddings_clusters_, hdbscan_params):
    logger.info(f"clustering embedding_viz shape: {embeddings_.value.shape}")
    logger.info(f"clustering options {hdbscan_params}")
    labels = cluster(embeddings_.value, options=hdbscan_params.model_dump())
    embeddings_clusters_.value = labels


@solara.component
def Hdbscan(embeddings_, embeddings_clusters_):
    """Manage Clustering Algorithm (HDBSCAN)."""
    min_samples = solara.use_reactive(2)
    min_cluster_size = solara.use_reactive(2)
    max_cluster_size = solara.use_reactive(20)
    hdbscan_params = HdbscanParams(
        min_samples=min_samples.value,
        min_cluster_size=min_cluster_size.value,
        max_cluster_size=max_cluster_size.value,
    )

    with solara.Column() as component:
        with solara.Row(style="display: flex; align-items: center;"):
            solara.Text("hdbscan", style="font-size: 14px;")
            with solara.Tooltip("Run Hdbscan"):
                    solara.Button(
                        icon_name="mdi-play",
                        icon=True,
                        on_click=partial(
                        run_hdbscan, embeddings_, embeddings_clusters_, hdbscan_params
                    ),
            )
        with solara.Row():
            solara.InputInt(label="min_samples", value=min_samples)
            solara.InputInt(label="min_cluster_size", value=min_cluster_size)
            solara.ProgressLinear(run_hdbscan.pending)
    return component

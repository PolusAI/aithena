"""Reduction Algorithms and Components."""

from functools import partial
from typing import get_args

import solara
from ai_review_app.utils.common import get_logger
from solara.lab import task

from ai_review_app.services.visualize import DistanceMetrics, UmapParams, reduce

logger = get_logger(__file__)


# list of distance metrics
METRICS: list[DistanceMetrics] = list(get_args(DistanceMetrics))


@task
async def run_umap(umap_params_, embeddings_):
    """backend call to umap."""
    logger.info("run umap...")
    logger.info(f"umap options: {umap_params_.model_dump()}")
    embeddings_.value = reduce(embeddings_.value, umap_params_.model_dump())
    logger.info(f"nb of embeddings_viz : {len(embeddings_.value)}")


@solara.component
def Umap(embeddings_):
    """Manage Dimension Reduction Algorithm (UMAP)."""
    # TODO ability reset to original dimension. See how we want to manage reseting labels

    # TODO create default state
    n_components = solara.use_reactive(2)
    metric = solara.use_reactive("cosine")
    min_dist = solara.use_reactive(0.0)
    n_neighbors = solara.use_reactive(3)

    with solara.Column() as umap:
        with solara.Row(style="display: flex; align-items: center;"):
            solara.Text("umap", style="font-size: 14px;")
            with solara.Tooltip("Run UMAP"):
                    solara.Button(
                        icon_name="mdi-play",
                        icon=True,
                        on_click= partial(
                            run_umap,
                            UmapParams(
                                n_components=n_components.value,
                                n_neighbors=n_neighbors.value,
                                metric=metric.value,
                                min_dist=min_dist.value,
                            ),
                            embeddings_,
                        ),
            )
        with solara.Row():
            solara.InputInt(label="n_components", value=n_components)
            solara.Select(label="metric", values=METRICS, value=metric)
            solara.InputFloat(label="min_dist", value=min_dist)
            solara.InputInt(label="n_neighbors", value=n_neighbors)
        solara.ProgressLinear(run_umap.pending)
    return umap

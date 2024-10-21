"""Plotting functions and components for the AI Review dashboard."""

# pylint: disable=C0103, W0106, C0116, W1203, R0913, R0914, R0915, W0613

from typing import Callable

import numpy as np
import pandas as pd
import plotly.express as px
import solara
from pydantic import BaseModel
from ai_review_app.utils.common import get_logger
from ai_review_app.models.context import Document

logger = get_logger(__file__)


class PointSelection(BaseModel):
    """Represent selection objects in the scatter plot."""

    row: int


@solara.component
def ScatterPlot(
    embeddings_: np.ndarray,
    labels_: list[int],
    documents_: list[Document],
    on_select_: Callable,
):
    """Interactive Scatter Plot."""

    def format_tooltip_data(text: str, line_width: int = 60, max_characters: int = 160):
        max_length = min(max_characters, len(text))
        suffix = "..." if max_length > len(text) else ""
        text = text[:max_length]
        text = '<br> '.join(text[i:i + line_width] for i in range(0, len(text), line_width)) 
        return text + suffix

    # Scatter plot works from a dataframe
    # NOTE we need to lift that to top level so we can sort and edit as a dataframe.
    assert (
        embeddings_.shape[0] == len(labels_)
        and len(documents_) == len(labels_)
    )

    df_ = pd.DataFrame(embeddings_)
    df_["id"] = [format_tooltip_data(doc.title) for doc in documents_]
    df_["text"]  = [format_tooltip_data(doc.text) for doc in documents_]
    df_["labels"] = [str(label) for label in labels_]

    # logger.info(df_)
    logger.info("dataframe rebuilt...")

    # TODO check: labels are just sequential integer, add a better color map?
    fig = px.scatter(
        df_,
        x=0,
        y=1,
        color="labels",
        hover_data=["id", "labels", "text"],
    )

    # tooltip template when hovering
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br><br><b>label:</b>%{customdata[1]}<br>%{customdata[2]}<extra></extra>"
    )

    fig.update_layout(
        hoverlabel={"align": "left", "font": {"family": "Roboto", "size": 12}}
    )

    def select_points(click_data):
        logger.info(f"selection action ing graph view : {click_data}")
        xs = click_data["points"]["xs"]
        ys = click_data["points"]["ys"]


        selected_indices = []
        # Iterate over the values in xs and ys
        for x, y in zip(xs, ys):
            indices = df_.index[(df_[0] == x) & (df_[1] == y)].tolist()
            selected_indices.extend(indices)
        selected_points = [PointSelection(row=row_index) for row_index in selected_indices]
        logger.debug(f"selected points: {selected_points}")
        selected_documents=[documents_[x.row] for x in selected_points]
        on_select_(selected_documents)

    return solara.FigurePlotly(fig, on_click=select_points, on_selection=select_points)

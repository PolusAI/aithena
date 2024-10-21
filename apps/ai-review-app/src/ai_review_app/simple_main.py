"""
Ai literature review dashboard.
"""

# pylint: disable=C0103, W0106, C0116, W1203, R0913, R0914, R0915, W0613

import datetime
from pathlib import Path
from functools import partial
from typing import cast

from ai_review_app.components.context_manager import ContextView
from ai_review_app.models.context import Context
from ai_review_app.utils.exceptions import IncorrectEmbeddingDimensionsError
import solara
from solara.alias import rv

from aithena_services.llms.types.message import BaseMessage, UserMessage

import ai_review_app.config as config 
from ai_review_app.components.cluster import Hdbscan, knn_search
from ai_review_app.utils.common import get_logger
from ai_review_app.components import Selections
from ai_review_app.components.llm_assistant import LLMSideBar
from ai_review_app.components.plot import ScatterPlot
from ai_review_app.components.reduce import Umap
from ai_review_app.utils import (
    get_records,
    get_valid_collection,
)
from ai_review_app.components.database import COLLECTIONS, CollectionInfo, SearchBox, SelectCollections

logger = get_logger(__file__)

contexts: solara.Reactive[list[Context]] = solara.reactive(
    cast(list[BaseMessage], [Context()])
)

current_context: solara.Reactive[Context] = solara.lab.Ref(contexts.fields[-1])

message_history: solara.Reactive[list[BaseMessage]] = solara.lab.Ref(
    cast(list[BaseMessage], current_context.fields.message_history)
)

current_llm_name: solara.Reactive[str] = (
    solara.reactive("llama3.1")
    if "llama3.1" in config.LLM_DICT
    else solara.reactive(list(config.LLM_DICT.keys())[0])
)

title = "AI Literature Review Assistant"

def add_message(message_history: solara.Reactive[list[BaseMessage]]):
    message = f"Message {len(message_history.value)}"
    message_history.value = [*message_history.value, UserMessage(content=message)]

def add_context(contexts: solara.Reactive[list[Context]]):
    contexts.value = [*contexts.value, Context(created=datetime.datetime.now())]

def delete_context(contexts: solara.Reactive[list[Context]]):
    contexts.value = [*contexts.value][:-1]


@solara.component
def Page():
    """Main component rendering the whole page."""
    
    logger.debug("Rendering page...")

    # dynamic layout
    full_width = 12
    left_panel_width = 6
    right_panel_width = full_width - left_panel_width
    panel_0_height = 12
    panel_1_height = 12
    grid_layout_initial = [
        {
            "h": panel_0_height,
            "i": "0",
            "moved": False,
            "w": left_panel_width,
            "x": 0,
            "y": 0,
        },  # source_panel
        {
            "h": panel_1_height,
            "i": "1",
            "moved": False,
            "w": right_panel_width,
            "x": left_panel_width,
            "y": 0,
        },  # viz_controls
        {
            "h": 12,
            "i": "2",
            "moved": False,
            "w": 6,
            "x": 0,
            "y": panel_0_height,
        },  # selection_panel
        {
            "h": 12,
            "i": "3",
            "moved": False,
            "w": 6,
            "x": 6,
            "y": panel_1_height,
        },  # viz_scatter
    ]

    # db related state
    collection, set_collection = solara.use_state(
        solara.use_memo(
            lambda: get_valid_collection(COLLECTIONS), dependencies=COLLECTIONS
        )
    )  # run once since db connections are handled at startup.
    
    records = solara.reactive(
        solara.use_memo(
            partial(get_records, collection), collection, debug_name="get_records"
        )
    )  # refresh only when a different collection is selected

    no_records = solara.use_reactive(False)
    if len(records.value) == 0:
        no_records.value = True

    

    with solara.Column(style={"padding": "15px"}) as main:
        with solara.lab.Tabs():
        
            with solara.lab.Tab("Documents"):

                """Data source info."""
                with rv.Card(
                    style_="width: 100%; height: 100%; padding: 8px"
                ) as source_panel:
                    solara.Markdown("## **Data**")
                    if no_records.value:
                        solara.Warning("No records found in the collection.")
                    solara.Button(
                        "Find similar document",
                        on_click=partial(knn_search, collection, records),
                    )

                    SelectCollections(COLLECTIONS, collection, set_collection)

                    logger.info(f"################# {message_history.value}")

                    solara.Button("New message", on_click=lambda: add_message(message_history))

                    solara.Button("New context", on_click=lambda: add_context(contexts))
                    solara.Button("Delete current context", on_click=lambda: delete_context(contexts))
                    ContextView(current_context.value)
                    for context in contexts.value:
                        solara.Markdown(f"{context.name} - {context.created.strftime('%Y-%m-%d %H:%M:%S')}") 

        return main



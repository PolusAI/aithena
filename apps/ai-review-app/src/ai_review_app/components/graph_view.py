from functools import partial
from typing import Callable
from ai_review_app.components.plot import ScatterPlot
import solara
from solara.alias import rv

@solara.component
def GraphView(
    embeddings_viz,
    embeddings_viz_labels,
    documents,
    selected_documents,
    summarize_clusters: Callable):    
    
    def add_to_selected_documents(docs):
        """Add documents to the current context selected documents."""
        docs_dict = {doc.id : doc for doc in docs}
        selected_documents.value = {**selected_documents.value, **docs_dict}    
    
    if (
        embeddings_viz.value is not None
        and embeddings_viz.value.shape[1] == 2
    ):
        with solara.Row(style="display: flex; align-items: center;"):
            rv.CardTitle(children=["View"])
            with solara.Tooltip("Summarize all: summarize all cluster of documents. "):
                solara.Button(
                    icon_name="mdi-folder-settings",
                    icon=True,
                    on_click=summarize_clusters
                )
        if summarize_clusters.pending:
            solara.Button("Cancel", on_click=summarize_clusters.cancel)
        solara.ProgressLinear(summarize_clusters.pending)
        ScatterPlot(
            embeddings_viz.value,
            embeddings_viz_labels.value,
            documents,
            on_select_=add_to_selected_documents,
        )
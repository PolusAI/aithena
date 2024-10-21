"""
Ai literature review dashboard.
"""

# pylint: disable=C0103, W0106, C0116, W1203, R0913, R0914, R0915, W0613

from collections import defaultdict
import datetime
import json
from pathlib import Path
from functools import partial
from typing import Union, cast
import uuid

from ai_review_app.components.context_manager import ContextManager, DocView, LeftMenu
from ai_review_app.components.graph_view import GraphView
from ai_review_app.llm.summarize import summarize_all
from ai_review_app.models.prompts import PROMPT_LABEL, PROMPT_SINGLE_LABEL, PROMPT_SINGLE_SUMMARY, PROMPT_SUMMARY
from ai_review_app.models.context import Context, DocType, Document, SimilarDocument
from ai_review_app.models.records import get_records, get_valid_collection, get_valid_collections
from ai_review_app.services.call_llm import call_llm
from ai_review_app.services.document_factory import convert_records_to_docs
from ai_review_app.utils.exceptions import IncorrectEmbeddingDimensionsError
from aithena_services.llms.types.base import AithenaLLM

import requests
from solara.lab import task
import numpy as np
import pandas as pd
import solara
from solara.alias import rv
from aithena_services.llms.types import Message
from qdrant_client.http.models.models import Record

import ai_review_app.config as config 
from ai_review_app.components.cluster import Hdbscan, knn_search
from ai_review_app.utils.common import get_logger
from ai_review_app.components.chatbot_sidebar import ChatBotSideBar
from ai_review_app.llm import OLLAMA_AVAILABLE_MODELS, build_outline
from ai_review_app.components.plot import ScatterPlot
from ai_review_app.components.reduce import Umap
from ai_review_app.components.database import COLLECTIONS, CollectionInfo, SearchBox, SelectCollections
from ai_review_app.config import SUMMARY_CUTOFF
# from polus.ai.services.embed.embed_nvembed import EmbedderNvEmbed


logger = get_logger(__file__)

class EmbeddingServiceOllama:

    """Embedding service using Ollama."""
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.embed_url= endpoint + "/api/embed"
        self.healthcheck_url= endpoint + "/api/tags"

    def healthcheck(self) -> bool:
        requests.get(self.healthcheck_url)

    def embed_all(self, instruct_queries: list[tuple[str,str]], batch_size: int = 1 ) -> requests.Response:
        """Embed data.
        
        The signature convert to old convert service for compatiblity.
        """
        docs = [q[1] for q in instruct_queries]
        payload = {"model": "nomic-embed-text", "input": docs}
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.embed_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        result = response.json()["embeddings"]
        logger.debug(f"response in {response.elapsed.total_seconds()} sec. for batch of size {np.array(result).shape}")
        return result

"""Initialize the embedding service."""
# try:
#     embedding_service = EmbedderNvEmbed(1)
#     # embedding_service = EmbeddingServiceOllama(config.OLLAMA_SERVICE_URL)
#     # embedding_service.healthcheck()
#     logger.error("!!!!!!!!!!!!!!!! Embedding service ready.")
# except Exception as e:
#     embedding_service = None
#     logger.error("!!!!!!!!!!!!!!!! Could not instantiate embedding service.")
#     logger.exception(e)
#     exit()

# embedding_service_available = solara.reactive(embedding_service is not None)
embedding_service_available = solara.reactive(False)

"""All contexts managed by the app."""
contexts: solara.Reactive[list[Context]] = solara.reactive(
    cast(
        list[Context],
        [Context(name = uuid.uuid4().hex, created=datetime.datetime.now())]
    )
)

"""Current context."""
current_context: solara.Reactive[Context] = solara.lab.Ref(contexts.fields[-1])

"""The message history for the current context"""
message_history: solara.Reactive[list[Message]] = solara.lab.Ref(
    cast(list[Message], current_context.fields.message_history)
)

"""The selected documents (reference to the current context documents)."""
selected_documents: solara.Reactive[dict[str,Document]] = solara.lab.Ref(current_context.fields.documents)

"""The responses to a user search query."""
query_responses: solara.Reactive[dict[str,SimilarDocument]] = solara.reactive(cast(dict[str,SimilarDocument], {}))

warning_message:  solara.Reactive[str] = solara.reactive("")

"""The name of the current llm."""
current_llm_name: solara.Reactive[str] = (
    solara.reactive("azure/gpt-4o")
    if "azure/gpt-4o" in config.LLM_DICT
    else solara.reactive(list(config.LLM_DICT.keys())[0])
)

"""The llm currently selected."""
current_llm: solara.Reactive[AithenaLLM] = solara.reactive(  # type: ignore
    config.LLM_DICT[current_llm_name.value]
)

title = "AI Literature Review Assistant"



@solara.component
def Page():
    """Main component rendering the whole page."""

    # TODO split in two function as the instance check is unreliable
    def do_label(docs: Union[Document|dict[str,Document]]):
        """Label the selected documents."""
        if isinstance(docs, dict):
            context = Context(prompt=PROMPT_LABEL)
            context.documents = {doc.id: doc for doc in docs.values()}
        else:
            context = Context(prompt=PROMPT_SINGLE_LABEL)
            context.documents = {docs.id: docs}

        system_prompt = context.to_markdown()
        messages = [Message({"role": "system", "content": system_prompt})]
        response = call_llm(current_llm.value, messages)
        return response.message.content

    # TODO make that a background task with continuous update.
    # async def summarize_all(metadatas, labels, model, summaries, set_summaries):
    # also use async api with llm.
    @task
    async def summarize_clusters():
        await summarize_all(documents, embeddings_viz_labels.value, current_llm.value, contexts, summaries)     

    # TODO split in two function as the instance check is unreliable
    def summarize(docs: Union[Document|dict[str,Document]]):
        """Summarize the selected documents."""
        print(docs.__class__.__name__)
        if isinstance(docs, dict):
            context = Context(prompt=PROMPT_SUMMARY)
            context.documents = {doc.id: doc for doc in docs.values()}
        else:
            context = Context(prompt=PROMPT_SINGLE_SUMMARY)
            context.documents = {docs.id: docs}
        system_prompt = context.to_markdown()
        messages = [Message({"role": "system", "content": system_prompt})]
        response = call_llm(current_llm.value, messages)
        return response.message.content

    def similarity_search(doc: Document):
        """Search for similar documents."""
        found = False
        docs = []
        for rec in records.value:
            if rec.id == doc.id:
                found = True
                res = knn_search(rec.vector, collection)
                break
        if not found:
            raise Exception("doc in not part of the db. Similarity search does not handle custom doc at the moment.")
        for point in res.points:
            for doc in documents:
                if point.id == doc.id:
                    docs.append(doc)
        return docs
    
    logger.debug("Rendering page...")

    """The outline document"""
    outline_doc: solara.Reactive[Document] = solara.use_reactive(None)

    """The current collection."""
    collection, set_collection = solara.use_state(
        solara.use_memo(
            lambda: get_valid_collection(COLLECTIONS), dependencies=COLLECTIONS
        )
    )
    
    """Records pulled from the selected collection."""
    records: solara.Reactive[list[Record]]  = solara.use_reactive(
        solara.use_memo(
            partial(get_records, collection), collection, debug_name="get_records"
        )
    )  # with use_memo : refresh only when a different collection is selected

    """Convert all records to documents."""
    documents : list[Document] = solara.use_memo(lambda : convert_records_to_docs(records.value), records.value, debug_name="convert_records_to_docs")

    def get_embeddings(records: list[Record]) -> np.ndarray[float]:
        """return a 2D numpy containing all the embeddings."""
        return np.array([record.vector for record in records])

    """Embeddings for all records."""
    embeddings : np.ndarray[float] = solara.use_memo(
        lambda: get_embeddings(records.value), dependencies=records.value, debug_name="records_embeddings"
    )

    assert len(documents) == len(embeddings)

    if embeddings.ndim != 2:
        # TODO no need for such specifc error, let's just have not recoverable error with custom message
        msg = f"Expected embeddings to be numpy array of shape(n_records, embedding_dim), Got: {embeddings.shape}"
        raise IncorrectEmbeddingDimensionsError(
            msg
        )
    
    """original embedding size."""
    embeddings_size : int = embeddings.shape[1]

    """embeddings used for visualization.
    For visualization, we only support 2D embeddings.
    If 2D embeddings are loaded, we can display them, otherwise we need to reduce dimensions first.
    """
    embeddings_viz: solara.Reactive[np.ndarray[float]] = solara.use_reactive(embeddings)
    if embeddings_size == 2:
        embeddings_viz.value = embeddings

    def init_labels() -> list[int]:
        """Initialize the labels for the embeddings."""
        return [ val for val in range(embeddings_viz.value.shape[0])]

    """Labels for embeddings clusters."""
    embeddings_viz_labels : solara.Reactive[list[int]] = solara.use_reactive(solara.use_memo(
        lambda: init_labels(), dependencies=embeddings_viz.value, debug_name="clusters"
    ))


    def build_docs_dataframe(documents: list[Document], labels: list[int]) -> pd.DataFrame:
        """Build a pandas dataframe for documents."""
        docs_as_dict = [doc.model_dump(exclude=["type", "similar_documents", "vector", "labels", "summary"]) for doc in documents]
        df = pd.DataFrame(docs_as_dict)
        if labels is not None:
            df["labels"] = [str(label) for label in labels]
        return df

    """Pandas dataframe for documents."""
    docs_df = solara.use_memo(partial(build_docs_dataframe, documents, embeddings_viz_labels.value), [documents, embeddings_viz_labels.value], debug_name="records_pandas_df")
    
    # TODO probably temp
    """Stored all summaries generated."""
    summaries : solara.Reactive[list[Context]] = solara.use_reactive([])

    """Sidebars visible."""
    show_sidebars: solara.Reactive[bool] = solara.use_reactive(False)


    """Component rendering the main page."""
    with solara.Column(style={"padding": "15px"}) as main:

        solara.Style(Path(__file__).parent.absolute() / "css" / "style.css") #remove solara text

        LeftMenu(children=[
            ContextManager(
                contexts,
                current_context,
                message_history,
                selected_documents,
                similarity_search=similarity_search,
                summarize=summarize,
                do_label=do_label,
                )], sidebar=show_sidebars)
        
        with solara.Row():
            ChatBotSideBar(
                show_sidebars,
                current_llm_name,
                current_llm, 
                current_context,
                message_history
            )


        tab_index = solara.use_reactive(0)
        tab_count = 5

        def goto_tab(index):
            if index < 0 or index >= tab_count:
                index = 0
            tab_index.value = index

        def next_tab():
            tab_index.value = (tab_index.value + 1) % tab_count

        with solara.lab.Tabs(value=tab_index):
            
            with solara.lab.Tab("Document Source"):
                with solara.Row():
                    """Data source info."""
                    with rv.Card(
                        style_="width: 100%; height: 100%; padding: 8px"
                    ) as data_source:
                        rv.CardTitle(children=["Data Source"])
                        if len(records.value) == 0:
                            solara.Warning("No records found in the collection.")

                        SelectCollections(get_valid_collections(COLLECTIONS), collection, set_collection)
                        CollectionInfo(collection, records.value, embeddings)

                    """Data visualization controls."""
                    with rv.Card(
                        style_="width: 100%; height: 100%; padding: 8px"
                    ) as preprocessing:
                        rv.CardTitle(children=["Preprocess"])
                        Umap(embeddings_viz)
                        Hdbscan(embeddings_viz, embeddings_viz_labels)

                """Data visualization."""
                with rv.Card(
                    style_="width: 100%; height: 100%; padding: 8px"
                ) as visulization:
                    GraphView(embeddings_viz, embeddings_viz_labels, documents, selected_documents, summarize_clusters)

            """Tab to display documents."""
            with solara.lab.Tab("Documents"):
                solara.DataFrame(docs_df, items_per_page=100)

            """Tab to query db."""
            with solara.lab.Tab("Search"):
                if embedding_service_available.value:
                    SearchBox(embedding_service, collection, query_responses)

                for doc in list(query_responses.value.values()):
                    DocView(
                        doc.document,
                        selected_documents,
                        score=doc.score,
                        do_label=do_label,
                        summarize=summarize,
                        )

            """Tab to display all generated summaries."""
            with solara.lab.Tab("Summaries"):
                for sum in summaries.value:
                    with solara.Card():
                        doc_ids_list = ("\n* ").join([doc.id for doc in sum.documents.values() if doc.type != DocType.SUMMARY])
                        solara.Markdown(doc_ids_list)
                        summary = [doc for doc in sum.documents.values() if doc.type == DocType.SUMMARY][0]
                        if summary:
                            DocView(summary, selected_documents)

            """Final Review Markdown editor."""   
            with solara.lab.Tab("Editor"):
                solara.Button(
                    "Generate outline",
                    on_click=partial(
                        build_outline, contexts, summaries, current_llm, outline_doc
                    ),
                )

                ManagedMarkdownEditor(outline_doc=outline_doc)
 
        if warning_message.value:
            solara.Warning(warning_message.value)

    return main

@solara.component
def ManagedMarkdownEditor(outline_doc: solara.Reactive[Document]):

    edit_mode = solara.use_reactive(False)
    content, set_content = solara.use_state_or_update("")

    def update_final_doc(text):
        set_content(text)

    def save_doc():
        logger.info("doc saved.")

    if outline_doc.value:
        DocView(outline_doc.value, selected_documents)

    with solara.Column():
        with solara.Row():
            with solara.Tooltip("Save"):
                solara.Button(
                    icon_name="mdi-content-save",
                    icon=True,
                    on_click=lambda : save_doc()
                )
        with rv.Sheet(elevation=2):
                solara.MarkdownEditor(
                    value=content, on_value=update_final_doc
                )


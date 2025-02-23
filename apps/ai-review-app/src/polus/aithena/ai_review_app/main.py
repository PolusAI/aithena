"""
Ai literature review dashboard.
"""

# pylint: disable=C0103, W0106, C0116, W1203, R0913, R0914, R0915, W0613
import datetime
import json
from pathlib import Path
from functools import partial
from typing import Union, cast
import uuid

import numpy as np
import pandas as pd
from polus.aithena.ai_review_app.utils.common import current_date, current_time
import solara
from solara.alias import rv
from solara.lab import task
from qdrant_client.http.models.models import Record



import polus.aithena.ai_review_app.config as config 

from polus.aithena.ai_review_app.components.context_manager import ContextManager, DocView, LeftMenu
from polus.aithena.ai_review_app.components.graph_view import GraphView
from polus.aithena.ai_review_app.components.cluster import Hdbscan, knn_search
from polus.aithena.ai_review_app.components.reduce import Umap
from polus.aithena.ai_review_app.components.database import COLLECTIONS, CollectionInfo, SearchBox, SelectCollections
from polus.aithena.ai_review_app.components.chatbot_sidebar import ChatBotSideBar
from polus.aithena.ai_review_app.components.database import db

from polus.aithena.ai_review_app.models.context import Context, DocType, Document, SimilarDocument
from polus.aithena.ai_review_app.models.prompts import PROMPT_LABEL, PROMPT_SUMMARY, PROMPT_OUTLINE, PROMPT_CHAT

from polus.aithena.ai_review_app.services.aithena_services_client import chat_request, get_chat_models
from polus.aithena.ai_review_app.services.document_factory import convert_records_to_docs
from polus.aithena.ai_review_app.services.summarize import build_outline, summarize_all
from polus.aithena.ai_review_app.services.embed import IncorrectEmbeddingDimensionsError

from polus.aithena.common.logger import get_logger
from polus.aithena.common.utils import init_dir

# from polus.aithena.ai_review_app.services.embedding_service import EmbeddingServiceOllama

logger = get_logger(__file__)

"""Initialize the embedding service."""
# try:
#     embedding_service = EmbeddingServiceOllama(config.OLLAMA_SERVICE_URL)
#     embedding_service.healthcheck()
#     embedding_service_available = solara.reactive(embedding_service is not None)
#     logger.debug("Embedding service ready.")
# except Exception as e:
#     embedding_service = None
#     logger.error("Could not instantiate embedding service.")
#     logger.exception(e)
#     exit()

"""Disabled as all data are embedded with nvembed, which is unavailable in ollama."""
embedding_service_available = solara.reactive(False)

"""All contexts managed by the app."""
contexts: solara.Reactive[list[Context]] = solara.reactive(
    cast(
        list[Context],
        [Context(name = uuid.uuid4().hex, created=datetime.datetime.now())]
    )
)

"""Available chat models."""
chat_models : solara.Reactive[list[str]] = solara.reactive(get_chat_models())

def get_valid_model(models: list[str]):
    """if a default model is set in the config, use it."""
    if config.DEFAULT_CHAT_MODEL and config.DEFAULT_CHAT_MODEL in models:
        return config.DEFAULT_CHAT_MODEL
    return chat_models.value[0]

"""The name of the current llm."""
current_llm_name: solara.Reactive[str] = (
    solara.reactive(get_valid_model(chat_models.value))
)

"""Current context."""
current_context: solara.Reactive[Context] = solara.lab.Ref(contexts.fields[-1])

"""The message history for the current context."""
message_history: solara.Reactive[list[dict]] = solara.lab.Ref(
    cast(list[dict], current_context.fields.message_history)
)

"""Document in the current context."""
selected_documents: solara.Reactive[dict[str,Document]] = solara.lab.Ref(current_context.fields.documents)

"""Result of a similiraity search by the user."""
query_responses: solara.Reactive[dict[str,SimilarDocument]] = solara.reactive(cast(dict[str,SimilarDocument], {}))

warning_message:  solara.Reactive[str] = solara.reactive("")

def get_valid_collections(collections: list[str]):
    """Return a list of valid collections."""
    return collections

def get_default_collection(collections: list[str]):
    """Return a collection according to the default configuration."""
    if config.DEFAULT_COLLECTION and config.DEFAULT_COLLECTION in collections:
        logger.info(f"default collection: {config.DEFAULT_COLLECTION}")
        return config.DEFAULT_COLLECTION
    logger.info(f"select first collection : {collections[0]}")
    return collections[0]

def get_records(collection: str) -> list[Record]:
    """Retrieve records for a given collection."""
    logger.info(f"##### retrieve records for collection {collection}...")
    return db.get_all_records(collection)

title = "AI Literature Review Assistant"

@solara.component
def PromptConfig(
    title: str,
    prompt: solara.Reactive[str],
):
    edit_mode = solara.use_reactive(False)
    display_prompt = solara.use_reactive(False)
    _prompt = solara.use_reactive(prompt.value)

    def edit_prompt():
        edit_mode.value = True

    def save_prompt():
        edit_mode.value = False
        prompt.value = _prompt.value

    def update_doc(val):
        _prompt.value = val

    def view_prompt():
        """Show the prompt."""
        display_prompt.value = not display_prompt.value 

    with rv.Card():
        rv.CardTitle(children=[title])
        with solara.Row():
            with solara.Tooltip("Hide" if display_prompt.value else "Show"):
                solara.Button(
                    icon_name="mdi-eye-off" if display_prompt.value else "mdi-eye",
                    icon=True,
                    on_click=view_prompt,
                )
            with solara.Tooltip("Save" if edit_mode.value else "Edit"):
                solara.Button(
                    icon_name="mdi-content-save" if edit_mode.value else "mdi-pencil",
                    icon=True,
                    on_click=lambda : edit_prompt() if not edit_mode.value else save_prompt()
                )
                
            if edit_mode.value:
                solara.MarkdownEditor(
                    value=prompt.value, on_value=update_doc
                )

            if not edit_mode.value and display_prompt.value:
                solara.Markdown(prompt.value)

@solara.component
def Page():
    """Main component rendering the whole page."""

    async def do_label(docs: Union[Document|dict[str,Document]]):
        """Label the selected documents."""
        context = Context(prompt=prompt_label.value)
        if isinstance(docs, dict):
            context.documents = {doc.id: doc for doc in docs.values()}
        else:
            context.documents = {docs.id: docs}

        system_prompt = context.to_markdown()
        messages = [{"role": config.LLM_ROLE, "content": system_prompt}]
        response = chat_request(current_llm_name.value, messages)
        return response["message"]["content"]

    @task
    async def summarize_clusters():
        await summarize_all(documents, embeddings_viz_labels.value, current_llm_name.value, contexts, summaries, prompt_summary)     

    def summarize(docs: Union[Document|dict[str,Document]]):
        """Summarize the selected documents."""
        context = Context(prompt=prompt_summary.value)
        if isinstance(docs, dict):
            context.documents = {doc.id: doc for doc in docs.values()}
        else:
            context.documents = {docs.id: docs}
        system_prompt = context.to_markdown()
        messages = [{"role": config.LLM_ROLE, "content": system_prompt}]
        response = chat_request(current_llm_name.value, messages)
        return response["message"]["content"]

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
    logger.debug(f"current_llm_name: {current_llm_name.value}")

    """The outline document"""
    outline_doc: solara.Reactive[Document] = solara.use_reactive(None)

    """The current collection."""
    collection, set_collection = solara.use_state(
        solara.use_memo(
            lambda: get_default_collection(COLLECTIONS), dependencies=COLLECTIONS
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

    if embeddings.ndim != 2:
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
    
    """Stored all summaries generated."""
    summaries : solara.Reactive[list[Context]] = solara.use_reactive([])

    """Sidebars visible."""
    show_sidebars: solara.Reactive[bool] = solara.use_reactive(False)

    prompt_chat: solara.Reactive[str] = solara.use_reactive(PROMPT_CHAT)
    prompt_outline: solara.Reactive[str] = solara.use_reactive(PROMPT_OUTLINE)
    prompt_summary: solara.Reactive[str] = solara.use_reactive(PROMPT_SUMMARY)
    prompt_label: solara.Reactive[str] = solara.use_reactive(PROMPT_LABEL)
    

    """Component rendering the main page."""
    with solara.Column(style={"padding": "15px"}) as main:

        solara.Style(Path(__file__).parent.absolute() / "css" / "style.css") #remove solara text

        LeftMenu(children=[
            ContextManager(
                current_llm_name,
                chat_models,
                contexts,
                current_context,
                message_history,
                selected_documents,
                prompt_chat,
                similarity_search=similarity_search,
                summarize=summarize,
                do_label=do_label,
                )], sidebar=show_sidebars)
        
        with solara.Row():
            ChatBotSideBar(
                show_sidebars,
                current_llm_name,
                current_context,
                message_history
            )


        tab_index = solara.use_reactive(0)

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

            with solara.lab.Tab("Model Configuration"):
                PromptConfig("Default Chat Prompt", prompt_chat)
                PromptConfig("Outline Prompt", prompt_outline)
                PromptConfig("Summary Prompt", prompt_summary)
                PromptConfig("Label Prompt", prompt_label)
                

            """Tab to display documents."""
            with solara.lab.Tab("Documents"):
                solara.DataFrame(docs_df, items_per_page=100)

            """Tab to query db."""
            # with solara.lab.Tab("Search"):
            #     if embedding_service_available.value:
            #         SearchBox(embedding_service, collection, query_responses)

            #     for doc in list(query_responses.value.values()):
            #         DocView(
            #             doc.document,
            #             selected_documents,
            #             score=doc.score,
            #             do_label=do_label,
            #             summarize=summarize,
            #             )

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
                        build_outline, contexts, summaries, current_llm_name.value, outline_doc, prompt_outline
                    ),
                )

                if build_outline.pending:
                    solara.ProgressLinear(build_outline.pending)

                ManagedMarkdownEditor(collection=collection, outline_doc=outline_doc)
 
        if warning_message.value:
            solara.Warning(warning_message.value)

    return main

@solara.component
def ManagedMarkdownEditor(collection: str, outline_doc: solara.Reactive[Document]):

    content, set_content = solara.use_state_or_update("")

    def update_doc(text):
        set_content(text)

    def save_doc():
        if content != "":
            save = content
        else:
            save = outline_doc.value.text
        path = init_dir(config.APP_DATA_DIR / collection)
        with ( path / f"outline_{current_time()}.log").open("w+") as fw:
                fw.write(save)
        logger.debug(f"Saved outline. {save}.")
    
    with solara.Row():
        with solara.Tooltip("Persist to disk"):
            solara.Button(
                icon_name="mdi-content-save",
                icon=True,
                on_click=lambda : save_doc()
            )

    if outline_doc.value:
        DocView(outline_doc.value, selected_documents)
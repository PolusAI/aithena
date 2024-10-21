import datetime
import uuid
from ai_review_app.models.context import Context, DocType, Document
from ai_review_app.utils.common import display_date_from_datetime
import solara
from solara.alias import rv
from aithena_services.llms.types.message import Message, Role
from polus.aithena.common.logger import get_logger
from typing import Callable, Optional, Union, cast

logger = get_logger(__file__)

@solara.component
def StyledText(text: str, background_color: str, border_radius: str = "10px", padding: str = "10px"):
    with solara.Div(style={
        "background-color": background_color,
        "border-radius": border_radius,
        "padding": padding,
        "margin": "5px 0"
    }):
        solara.Text(text)

@solara.component
def PromptView(
    context: solara.Reactive[Context],
):
    edit_mode = solara.use_reactive(False)
    display_prompt = solara.use_reactive(False)
    prompt = solara.use_reactive(context.value.prompt)

    def edit_prompt():
        edit_mode.value = True

    def save_prompt():
        edit_mode.value = False
        updated_dict = {**context.value.model_dump(), 'prompt': prompt.value}
        updated = Context(**updated_dict)
        print(f"$$$$$$$$$$$$$$$$ {updated}")
        context.value = updated

    def update_doc(val):
        prompt.value = val

    def view_prompt():
        """Show the prompt."""
        display_prompt.value = not display_prompt.value 

    with rv.Card():
        rv.CardTitle(children=["prompt"])
        """the first message is a system prompt."""
        if context.value.prompt == 0:
            solara.Markdown("No prompt created")
        else:
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
def DocView(
    doc: Document,
    selected_documents: solara.Reactive[dict[str,Document]],
    is_current_context: bool = False,
    similarity_search: Union[Callable,None] = None,
    summarize: Union[Callable,None] = None,
    do_label: Union[Callable,None] = None,
    score: Optional[float] = None,
    ):
    """Show document details.

    ## Arguments

    * `title`: the document to view
    * `selected_documents`: the list of documents currently selected
    * `is_current_context`: is this document viewed as part of the context view. If yes, buttons will have different meaning.
        The trash button will be used to remove the doc from the context rather than deleting it.
    """

    """show/hide doc content"""
    id = solara.use_reactive(doc.id)
    display_content = solara.use_reactive(False)
    edit_mode = solara.use_reactive(False)
    similar_documents = solara.use_reactive(doc.similar_documents)
    summary = solara.use_reactive(doc.summary)
    labels = solara.use_reactive(cast(list[str],doc.labels))
    

    def select_doc(val):
        """Add to or remove from the current context."""
        if val:
            selected_documents.value = {doc.id: doc, **selected_documents.value}
        else:
            logger.info(f"removing {doc.id} from selection...")
            updated_selection = { d.id:d for d in selected_documents.value.values() if d.id != doc.id}
            selected_documents.value = updated_selection
    
    def delete_doc():
        """Delete document."""
        logger.info("need to implement. Deleting doc from the current workspace.")

    def view_doc_content():
        """Show the text content of a document."""
        display_content.value = not display_content.value 

    def edit_doc():
        edit_mode.value = True

    def save_doc():
        edit_mode.value = False
        updated_docs = {**{d_id: d for d_id, d in selected_documents.value.items() if d_id != doc.id}, doc.id: doc}
        selected_documents.value = updated_docs

    def update_doc(val):
        doc.text = val
    
    def label_doc():
        if do_label is not None:
            try:
                labels_str = do_label(doc)
                print(f"labels: {labels_str}")
                doc.labels = labels_str.split(",")
                labels.value = doc.labels
            except Exception as e:
                logger.exception("Label doc not yet handled.")        

    def summarize_doc():
        if summarize is not None:
            try:
                doc.summary = summarize(doc)
                summary.value = doc.summary
                print(f"summary {doc.summary}")
            except Exception as e:
                logger.exception("Summarize doc not yet handled.")

    def find_similar_doc():
        if similarity_search is not None:
            try:
                docs = similarity_search(doc)
                logger.info(f"found {len(docs)} similar documents...")
                doc.similar_documents = docs
                similar_documents.value = doc.similar_documents
            except Exception as e:
                logger.debug("Similarity search on custom doc not yet handled.")

    def render():
        subtitle = f"{doc.id}" if score is None else f"{doc.id} [score: {score}]"
        with solara.Card(subtitle=subtitle) as main:
            is_selected : bool = doc.id in selected_documents.value
            with solara.Row():
                if doc.type != DocType.USER_TEXT:
                    solara.Text(doc.title)  
                if not is_current_context:
                    with solara.Tooltip("Remove from current context" if is_selected else "Add to current context"):
                        solara.Checkbox(value=is_selected, on_value=select_doc, style="margin-top:0px; padding-top:0px;")
                    
            with solara.Row():
                with solara.Tooltip("Hide content" if display_content.value else "Show content"):
                    solara.Button(
                        icon_name="mdi-eye-off" if display_content.value else "mdi-eye",
                        icon=True,
                        on_click=view_doc_content,
                    )
                with solara.Tooltip("Save" if edit_mode.value else "Edit"):
                    if doc.type == DocType.USER_TEXT:
                        solara.Button(
                            icon_name="mdi-content-save" if edit_mode.value else "mdi-pencil",
                            icon=True,
                            on_click=lambda : edit_doc() if not edit_mode.value else save_doc()
                        )
                with solara.Tooltip("Remove from context" if is_current_context else "Delete"):
                    solara.Button(
                        icon_name="mdi-delete",
                        icon=True,
                        on_click=lambda : select_doc(False) if is_current_context else delete_doc() 
                    )

                if summarize is not None:  
                    with solara.Tooltip("Summarize"):
                        solara.Button(
                            icon_name="mdi-folder-settings",
                            icon=True,
                            on_click=lambda : summarize_doc()
                        )

                if do_label is not None:  
                    with solara.Tooltip("Label"):
                        solara.Button(
                            icon_name="mdi-label-variant-outline",
                            icon=True,
                            on_click=lambda : label_doc()
                        )

                if similarity_search is not None:    
                    with solara.Tooltip("Find similar documents" ):
                        solara.Button(
                            icon_name="mdi-file-find",
                            icon=True,
                            on_click=lambda : find_similar_doc() 
                        )

            if similar_documents.value:
                with solara.Column(gap="5px"):
                    chips_ = [rv.Chip(
                                children=[sim.id],
                                # filter=True,
                                # outlined=True,
                            )
                            for sim in similar_documents.value
                    ]
                    # rv.ChipGroup(
                    #     children=chips_,
                    #     column=True,
                    #     multiple=True,
                    # ) 

            if labels.value:
                with solara.Row(gap="5px"):
                    for label in labels.value:
                        StyledText(text=label, background_color="#2596be")

            if edit_mode.value:
                solara.MarkdownEditor(
                    value=doc.text, on_value=update_doc
                )

            if not edit_mode.value and display_content.value:
                solara.Markdown(f"""{doc.text}""")


    if summary.value and display_content.value:
        with solara.Tooltip(summary.value):
            render()
    else:
        render()



@solara.component
def ContextView(
    context: solara.Reactive[Context],
    selected_documents: solara.Reactive[dict[str,Document]],
    is_current_context = False,
    similarity_search: Union[Callable,None] = None,
    summarize: Union[Callable,None] = None,
    do_label: Union[Callable,None] = None
    ):
    """Show Context Details.
    
    ## Arguments

    * `context`: the context to view
    * `selected_documents`: the list of currently selected documents
    * `is_current_context`: is the context currently selected?
    """
    
    """show/hide message history"""
    display_message_history = solara.use_reactive(False)
    summary = solara.use_reactive(context.value.summary)
    labels = solara.use_reactive(cast(list[str], context.value.labels))

    def label_docs():
        if do_label is not None:
            try:
                labels_str = do_label(context.value.documents)
                print(f"labels: {labels_str}")
                context.value.labels = labels_str.split(",")
                labels.value = context.value
            except Exception as e:
                logger.exception("Label doc not yet handled.")        

    def summarize_docs():
        if summarize is not None:
            try:
                context.value.summary = summarize(context.value.documents)
                summary.value = context.value.summary
                print(f"summary {context.value.summary}")
            except Exception as e:
                logger.exception("Summarize doc not yet handled.")


    def view_message_history():
        """Show the text content of a document."""
        display_message_history.value = not display_message_history.value 

    def add_new_user_doc():
        doc = Document(type=DocType.USER_TEXT)
        selected_documents.value = {**selected_documents.value, doc.id : doc}

    with rv.Card():
        """Context Summary"""
        if summary.value:
            with solara.Tooltip(summary.value):
                rv.CardTitle(children=[f"{context.value.name}"])
                rv.CardSubtitle(children=[f"created : {display_date_from_datetime(context.value.created)}"])
        else:
            rv.CardTitle(children=[f"{context.value.name}"])
            rv.CardSubtitle(children=[f"created : {display_date_from_datetime(context.value.created)}"])

        with solara.Row():
            if summarize is not None:  
                with solara.Tooltip("Summarize"):
                    solara.Button(
                        icon_name="mdi-folder-settings",
                        icon=True,
                        on_click=lambda : summarize_docs()
            )

            if do_label is not None:  
                with solara.Tooltip("Label"):
                    solara.Button(
                        icon_name="mdi-label-variant-outline",
                        icon=True,
                        on_click=lambda : label_docs()
                    )

        if labels.value:
            with solara.Row(gap="5px"):
                for label in labels.value:
                    StyledText(text=label, background_color="#2596be")

        if summary.value:
            with solara.Card(title="Context summary"):
                solara.Markdown(summary.value)

        with rv.Card():
            rv.CardTitle(children=["documents"])
            with solara.Row():
                with solara.Tooltip("Create new document"):
                    solara.Button(
                        icon_name="mdi-plus",
                        icon=True,
                        on_click=add_new_user_doc,
                    )
            """view all documents stored in this context."""
            for doc in context.value.documents.values():
                DocView(doc=doc,
                        selected_documents=selected_documents,
                        is_current_context=is_current_context,
                        similarity_search=similarity_search,
                        summarize=summarize,
                        do_label=do_label)

        with rv.Card():
            rv.CardTitle(children=["message history"])
            if len(context.value.message_history) == 0:
                solara.Markdown("No message history")
            else:
                with solara.Row():
                    with solara.Tooltip("Display message history"):
                        solara.Button(
                            icon_name="mdi-eye-off" if display_message_history.value else "mdi-eye",
                            icon=True,
                            on_click=view_message_history,
                        )
                    solara.Markdown(f"{len(context.value.message_history)} in the message history")

                if display_message_history.value:
                    for message in context.value.message_history:
                        solara.Markdown(message.content)

        PromptView(context)

@solara.component
def ContextManager(
    contexts : solara.Reactive[list[Context]],
    current_context: solara.Reactive[Context],
    message_history: solara.Reactive[list[Message]],
    selected_documents: solara.Reactive[dict[str,Document]],
    similarity_search: Union[Callable,None] = None,
    summarize: Union[Callable,None] = None,
    do_label: Union[Callable,None] = None
    ):
    """Context Manager.
    
    ## Arguments

    * `contexts`: list all contexts.
    * `current_context`: context currently selected
    * `message_history`: current message history
    * `selected_documents`: currently selected documents
    """

    def add_context(contexts: solara.Reactive[list[Context]]):
        current_context = Context(name = uuid.uuid4().hex, created=datetime.datetime.now())
        contexts.value = [*contexts.value, current_context]
        

    def delete_context(contexts: solara.Reactive[list[Context]], to_delete: solara.Reactive[Context]):
        #TODO delete a context stored on disk
        context_ids = [c.name for c in contexts.value]
        logger.info(f"existing contexts : {context_ids}")
        name_to_delete = to_delete.value.name
        if len(contexts.value) > 1:
            updated_contexts = [c for c in contexts.value if c.name != name_to_delete]
            current_context.value = updated_contexts[0]
            contexts.value = updated_contexts
        else:
            logger.info("need to be implemented...")
            #TODO should reset message_history, prompt, selected docs 

    def select_current_context(context_name):
        for context in contexts.value:
            if context.name == context_name:
                updated_contexts = [c for c in contexts.value if c.name != context_name]
                contexts.value = [*updated_contexts, context]
                return
    
    with solara.Column():
        with solara.Row():
            available_contexts = [context.name for context in contexts.value]

            assert len(available_contexts) == len(contexts.value)
            
            """All actions available on the list of contexts."""
            solara.Select(
                label="Current Context",
                value=current_context.value.name,
                values=available_contexts,
                on_value=select_current_context,
            )
            with solara.Tooltip("Create new context"):
                solara.Button(
                    icon_name="mdi-playlist-plus",
                    icon=True,
                    on_click=lambda: add_context(contexts),
                )
            with solara.Tooltip("delete current context"):
                solara.Button(
                    icon_name="mdi-playlist-remove",
                    icon=True,
                    on_click=lambda: delete_context(contexts, current_context),
                )

        for context in contexts.value:
            solara.Markdown(f"**context {context.name}** - last updated : {context.created.strftime('%Y-%m-%d %H:%M:%S')}")

        ContextView(current_context, selected_documents, True, similarity_search, summarize, do_label)




# TODO move to a layout file
@solara.component
def LeftMenu(children, sidebar):
    """Display a left menu."""
    rv.NavigationDrawer(
        children=children,
        v_model=sidebar.value, #show or hide
        fixed=True,
        right=False,
        floating=True,
        class_="customsidedrawer",
        width=550.0,
    )


"""SideBar Component for ai_review_app."""

# pylint: disable=C0103, W0106, C0116, W1203, R0913, R0914, R0915, W0613

from functools import partial
from typing import Callable
import solara
from solara.alias import rv
from ai_review_app.utils.common import get_logger

from chatbot_dash.components.editable_message import EditableMessage
from chatbot_dash.components.model_info import ModelInfo
from chatbot_dash.components.chat_options import ChatOptions
from aithena_services.llms.types.message import BaseMessage, UserMessage, AssistantMessage, Role

from ai_review_app.llm.ollama_utils import send_to_ollama
from ai_review_app.models.context import Document

from ai_review_app.llm import (
    AVAILABLE_PROMPTS,
    OLLAMA_AVAILABLE_MODELS,
    PROMPTS_DICT,
)


logger = get_logger(__file__)


@solara.component
def SendMessage(
    prompt,
    current_llm_name,
    current_llm,
    model,
    llm_context,
    set_llm_response,
    message_history,
    stop_streaming,
    message,
    set_message
):     
    with solara.Row(gap="0px"):

        def send_message(event, *args):
            msg = event.v_model
            set_message(msg)
            logger.info(f"Enter pressed, sending query: {msg}")
            # TODO change that
            send_to_ollama(
                prompt,
                model,
                llm_context,
                msg,
                set_llm_response,
                message_history,
                stop_streaming,
            )

        def click_send_btn(event, *args):
            if send_to_ollama.pending:
                logger.debug("Cancel last chat message.")
                #TODO this update the variable but does it cancel the request? This does not seem linked to an llm interaction.
                send_to_ollama.cancel
                # TODO CHECK if we can issue a query to chatbot to stop processing as well.
                return
            send_message(event, *args)

        text_area = rv.Textarea(
            label="Chat",
            filled=True,
            dense=False,
            rounded=True,
            append_outer_icon=(
                "mdi-send" if not send_to_ollama.pending else "mdi-stop-circle-outline"
            ),
            v_model=message,
            auto_grow=True,
            row_height="5px",
        )

        """start/cancel last request."""
        rv.use_event(
            text_area,
            "click:append-outer",
            click_send_btn,
        )

        """send user message"""
        rv.use_event(
            text_area,
            "keydown.enter.exact.prevent",
            send_message,
        )
    

@solara.component
def LLMTools(
    show: Callable,
    current_llm_name,
    current_llm,
    model,
    set_model,
    prompt_name,
    set_prompt_name,
    prompt,
    message_history: solara.Reactive[list[BaseMessage]],
    selected_documents : solara.Reactive[dict[str, Document]]
):
    with solara.Column(
        style={
            "width": "100%",
            "position": "relative",
            # "height": "calc(100vh - 50px)",
            "padding-bottom": "15px",
            "overflow-y": "auto",
        },
    ) as llm_tools:

        show_prompt, set_show_prompt = solara.use_state(False)
        user_context, set_user_context = solara.use_state("")
        markdown_records_context, set_markdown_records_context = solara.use_state("")
        llm_context, set_llm_context = solara.use_state("")
        edit_context, set_edit_context = solara.use_state(False)
        edit_prompt, set_edit_prompt = solara.use_state(False)
        llm_response, set_llm_response = solara.use_state("")
        show_debug, set_show_debug = solara.use_state(False)
        #TODO this should probably be a top-level state to handle canceling chat response on errors or other similar scenarii
        stop_streaming = solara.use_reactive(False) 
        message, set_message = solara.use_state(None)
        reset_on_change: solara.Reactive[bool] = solara.Reactive(False)
        """when set, make all assistant response editable."""
        # TODO CHECK rationale. Not sure how useful it is, as the previous conversation may become inconsitent.
        edit_mode: solara.Reactive[bool] = solara.Reactive(False)
        edit_index = solara.reactive(None)
        current_edit_value = solara.reactive("")
        model_labels: solara.Reactive[dict[int, str]] = solara.reactive({})

            # updated at each page refresh
        user_message_count = len([m for m in message_history.value if m.role == "user"])

        def call_llm():
            """Send chat history to the llm and update chat history with the response."""
            logger.info("############ call llm ##############")

            if user_message_count == 0:
                return
            
            context_documents = "\n".join([f"<DOC>{doc.id}: {doc.text}</DOC>" for doc in selected_documents.value.values()])
            # TODO add system prompt
            extended_prompt = f"""{prompt} <context>{context_documents}</context>"""

            if message_history.value[0].role != Role.SYSTEM and message_history.value[0].content == prompt:
                raise Exception("first message should be system and should be equal to prompt.")
            
            messages = [message.model_dump() for message in message_history.value]
            messages[0]["content"] = extended_prompt

            logger.debug(f"!!!!!!!!!! \n calling llm with  extended prompt : {messages}")
            
            response = current_llm.value.stream_chat(messages=messages)

            logger.debug("received a response from the llm, streaming...")
            message_history.value = [
                *message_history.value,
                AssistantMessage(content=""),
            ]
            for chunk in response:
                if chunk:
                    update_response(chunk.delta)


        def update_response(chunk: str):
            """Add next chunk to current llm response.
            This is needed when we are using LLMs in stream mode.
            """
            message_history.value = [
                *message_history.value[:-1],
                AssistantMessage(
                    content = message_history.value[-1].content + chunk,
                ),
            ]

        logger.debug("response completed...")

        def create_user_message(message):
            """"Update the message history with a new user message."""
            message_history.value = [
                *message_history.value,
                UserMessage(content=message),
            ]
            logger.debug(f"create a new user message: {message}")

        def select_prompt():
            """event handler. Triggered when the selected prompt changes."""
            if prompt_name not in PROMPTS_DICT:
                return
            prompt.value = PROMPTS_DICT[prompt_name]

        solara.use_effect(select_prompt, [prompt_name])

        def update_llm_context():
            # TODO CHECK/UPDATE
            llm_context_ = user_context + markdown_records_context
            set_llm_context(llm_context_)

        solara.use_effect(update_llm_context, [user_context, markdown_records_context])

        def reset_llm_state(*args):
            message_history.value = []
            set_llm_response("")
            set_message("")
            logger.debug("message history reset")

        with solara.Row(
            style={"padding-top": "6px", "padding-right": "5px"}, justify="end"
        ):
            btn = HideSideBarButton(show)

        solara.Switch(label="Show Debug", value=show_debug, on_value=set_show_debug)
        if show_debug:
            with solara.Column(gap="0px"):
                solara.Markdown("Debug")
                solara.Markdown("Selected for context:")
                solara.display([str(id) for id in selected_documents.value.keys()])
                solara.Markdown("LLM Context:")
                solara.display(llm_context)
                solara.Markdown("User Context")
                solara.display(user_context)

        """Select a LLM model amongst available options."""
        solara.Select(
            label="LLM Model",
            values=OLLAMA_AVAILABLE_MODELS,
            value=model,
            on_value=set_model,
        )

        """Select a canned prompt to guide llm response."""
        solara.Select(
            label="Prompt",
            values=AVAILABLE_PROMPTS,
            value=prompt_name,
            on_value=set_prompt_name,
        )

        """Whether to display selected prompt."""
        solara.Switch(label="Show Prompt", value=show_prompt, on_value=set_show_prompt)
        
        """Display selected prompt."""
        if show_prompt:
            with solara.Column(gap="0px"):
                solara.Markdown("### Prompt")
                if not edit_prompt:
                    if prompt.value == "":
                        solara.Markdown("No Prompt")
                    else:
                        solara.Markdown(f"```{prompt.value}```")
                    solara.Button(label="Edit", on_click=partial(set_edit_prompt, True))
                else:
                    solara.MarkdownEditor(prompt.value, prompt.value)
                    solara.Button(
                        label="Save", on_click=partial(set_edit_prompt, False)
                    )

        """View and Edit LLM Context."""
        solara.Markdown("## Context for LLM")
        if not edit_context:
            """display full context (user defined + documents)"""
            # TODO maybe it is confusing to present records as texts. display context from a context viewer component.
            solara.Markdown(markdown_records_context)

        """Chat with the LLM."""

        """Chat Bot top-level options"""
        with solara.Row(
            style={
                "display": "flex",
                "justify-content": "space-between",
            }
        ):
            solara.Markdown("## ChatBot")
            rhb = rv.Btn(
                children=[rv.Icon(children=["mdi-restore"])],
                icon=True,
                style_="top: 20px; left: 2px;",
            )
            rv.use_event(rhb, "click", reset_llm_state)


        SendMessage(
            prompt.value,
            current_llm_name,
            current_llm,
            model,
            llm_context,
            set_llm_response,
            message_history,
            stop_streaming,
            message,
            set_message
        )

        if llm_response != "":
            solara.Markdown("## LLM Response")
            solara.Markdown(llm_response)
        
        ChatOptions(current_llm_name, message_history, edit_mode, reset_on_change)

        with solara.lab.ChatBox():
            """Display message history."""
            for index, item in enumerate(message_history.value):
                is_last = index == len(message_history.value) - 1
                if index ==0  and item.role == "system": # do not display system prompt
                    logger.info("!!!!!!!!!!!!!! hide system prompt.")
                    continue
                if item.content == "": # do not display initial empty message content
                    continue
                with solara.Column(gap="0px"):
                    with solara.Div(style={"background-color": "rgba(0,0,0.3, 0.06)"}):
                        """Display a message.
                        NOTE ChatMessage work as a container, and has a children component.
                        For editable message, we pass on our component that will replace the 
                        default Markdown component that displays the message content.
                        """
                        with solara.lab.ChatMessage(
                            user=item.role == "user",
                            avatar=False,
                            name="Aithena" if item.role == "assistant" else "User",
                            color=(
                                "rgba(0,0,0, 0.06)"
                                if item.role == "assistant"
                                else "#ff991f"
                            ),
                            avatar_background_color=(
                                "primary" if item.role == "assistant" else None
                            ),
                            border_radius="20px",
                            style={
                                "padding": "10px",
                            },
                        ):
                            if edit_mode.value and item.role == "assistant":
                                EditableMessage(message_history, item.content, index, edit_index, current_edit_value)
                            else:
                                solara.Markdown(item.content)

                    if item.role == "assistant":
                        """display the model name under the llm response."""
                        if current_llm.value.class_name == "azure_openai_llm":
                            ModelInfo(
                                model_labels,
                                index,
                                f"azure/{current_llm.value.engine}",
                                task,
                                is_last,
                            )
                        else:
                            ModelInfo(model_labels, index, current_llm.value.model, task, is_last)


        """Anchor the chat input at the bottom of the screen."""
        solara.lab.ChatInput(
            send_callback=create_user_message,
            disabled=task.pending,
            style={
                "position": "fixed",
                "bottom": "0",
                "width": "100%",
                "padding-bottom": "5px",
            },
        )


    return llm_tools



@solara.component
def HideSideBarButton(set_sidebar):
    """Hide side bar."""
    def click_btn(*args):
        set_sidebar(False)

    btn = rv.Btn(
        children=[rv.Icon(children=["mdi-chevron-double-right"], size=38)],
        icon=True,
    )
    rv.use_event(btn, "click", click_btn)

@solara.component
def ShowSideBarButton(sidebar, set_sidebar):
    """Show side bar."""
    def click_navicon(*args):
        set_sidebar(not sidebar)

    show_sidebar_button = rv.AppBarNavIcon()
    rv.AppBar(
        children=[rv.Spacer(), show_sidebar_button],
        app=True,
    )
    rv.use_event(show_sidebar_button, "click", click_navicon)


@solara.component
def LLMSideBar(
    sidebar,
    set_sidebar,
    current_llm_name,
    current_llm,
    model,
    set_model,
    prompt_name,
    set_prompt_name,
    prompt,
    message_history,
    selected_documents
):
    """LLM assistant embedded in a side bar."""

    ShowSideBarButton(sidebar, set_sidebar)

    rv.NavigationDrawer(
        children=[
            LLMTools(
                set_sidebar,
                current_llm_name,
                current_llm,
                model,
                set_model,
                prompt_name,
                set_prompt_name,
                prompt,
                message_history,
                selected_documents
            )
        ],
        v_model=sidebar, #show or hide
        right=True,
        fixed=True,
        floating=True,
        class_="customsidedrawer",
        width=550.0,
    )

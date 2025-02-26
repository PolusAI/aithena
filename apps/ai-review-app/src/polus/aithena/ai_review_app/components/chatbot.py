"""Chatbot multiple models."""
# pylint: disable=E1129, E1120, C0116, C0103
import json
import typing
from polus.aithena.ai_review_app.services.aithena_services_client import chat_request_stream
from polus.aithena.common.logger import get_logger
import solara
import solara.lab
import solara
import reacton.ipyvuetify as rv

logger = get_logger(__file__)

@solara.component
def ModelInfo(model_labels, index: int, model: str, task, is_last: bool = False):
    """Display LLM info.
    Used to label LLM response.
    """
    
    # do not show label while we are streaming the last message response. 
    if not is_last or not task.pending:
        with solara.Row(
            gap="0px",
            style={
                "position": "relative",
                "width": "fit-content",
                "top": "-2",
                "height": "auto",
            },
        ):
            with solara.Div(
                style={
                    "position": "relative",
                    "width": "fit-content",
                }
            ):
                ModelLabel(model_labels, index, model, task, is_last)
                rv.Btn(
                    children=[
                        rv.Icon(
                            children=["mdi-creation"],
                        )
                    ],
                    icon=True,
                )

@solara.component
def ModelLabel(model_labels, index: int, model: str, task, is_last: bool = False):
    """Display the model name."""
    if index not in model_labels.value:
        model_labels.value.update({index: model})
    model_ = model_labels.value[index] if index in model_labels.value else model
    solara.Text(
        model_,
        style={
            "color": "rgba(0,0,0, 0.5)",
            "font-size": "0.8em",
            "position": "relative",
            "height": "fit-content",
            "width": "fit-content",
            "padding-left": "10px",
        },
    )


@solara.component
def ChatBot(
    messages : solara.Reactive[list[dict]],
    current_llm_name : solara.Reactive[str],
    on_response_completed: typing.Union[typing.Callable,None] = None
    ):

    """when set, history will be erased on model change."""
    reset_on_change: solara.Reactive[bool] = solara.reactive(False)

    """when set, make all assistant response editable."""
    current_edit_value = solara.reactive("")
    model_labels: solara.Reactive[dict[int, str]] = solara.reactive({})

    def send_message(message):
        """"Update the message history with a new user message."""
        messages.value = [
            *messages.value,
            {"role": "user", "content": message}
        ]
        logger.debug(f"create a new user message: {message}")
        call_llm()


    @solara.lab.task
    async def call_llm():
        response = chat_request_stream(current_llm_name.value, messages.value)
        messages.value = [
            *messages.value,
            {"role": "assistant", "content": ""}
        ]

        for line in response.iter_lines():
            logger.debug(f"Received line: {line}")
            if line:
                update_response_message(json.loads(line)["delta"])

        if on_response_completed is not None:
            on_response_completed(messages)

    def update_response_message(chunk: str):
        """Add next chunk to current llm response.
        This is needed when we are using LLMs in stream mode.
        """
        messages.value = [
            *messages.value[:-1],
            {"role": "assistant", "content": messages.value[-1]["content"] + chunk}
        ]

    with solara.Column(
        style={
            "width": "100%",
            "position": "relative",
            "height": "calc(100vh - 50px)",
            "padding-bottom": "15px",
            "overflow-y": "auto",
        },
    ):

        solara.ProgressLinear(call_llm.pending)

        with solara.lab.ChatBox():
            """Display message history."""
            for index, item in enumerate(messages.value):
                is_last = index == len(messages.value) - 1
                if item["role"] == "system": # do not display system prompt
                    continue
                if item["content"] == "": # do not display initial empty message content
                    continue
                with solara.Column(gap="0px"):
                    with solara.Div(style={"background-color": "rgba(0,0,0.3, 0.06)"}):
                        """Display a message.
                        NOTE ChatMessage work as a container, and has a children component.
                        For editable message, we pass on our component that will replace the 
                        default Markdown component that displays the message content.
                        """
                        with solara.lab.ChatMessage(
                            user=item["role"] == "user",
                            avatar=False,
                            name="Aithena" if item["role"] == "assistant" else "User",
                            color=(
                                "rgba(0,0,0, 0.06)"
                                if item["role"] == "assistant"
                                else "#ff991f"
                            ),
                            avatar_background_color=(
                                "primary" if item["role"] == "assistant" else None
                            ),
                            border_radius="20px",
                            style={
                                "padding": "10px",
                            },
                        ):
                            solara.Markdown(item["content"])

                    if item["role"] == "assistant":
                        """display the model name under the llm response."""
                        ModelInfo(model_labels, index, current_llm_name.value, call_llm, is_last)


        """Anchor the chat input at the bottom of the screen."""
        solara.lab.ChatInput(
            send_callback=send_message,
            disabled=call_llm.pending,
            style={
                "position": "fixed",
                "bottom": "0",
                "width": "100%",
                "padding-bottom": "5px",
            },
        )

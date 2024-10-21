"""Chatbot multiple models."""

# pylint: disable=E1129, E1120, C0116, C0103, E0401, R0914, W1203
import json
import logging
import os
from copy import copy
from functools import partial
from pathlib import Path
from typing import Callable

import requests  # type: ignore
import solara
import solara.lab
from component_utils import EditableMessage, ModelLabel, SelectOptions  # type: ignore
from solara.alias import rv

logger = logging.getLogger("aithena-agent-chat")
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger.setLevel(logging.DEBUG)

API_URL = os.getenv("AITHENA_SERVICES_URL", "http://localhost:8000")
API_URL = API_URL[:-1] if API_URL.endswith("/") else API_URL
logger.info(f"Started Aithena Chat Agent with API URL: {API_URL}")

FILE_PATH = Path(__file__).parent.absolute()

PROMPT_DEFAULT = """
You are an expert scientific assistant named Aithena.
Respond to users with knowledgeable, informative, and thoughtful answers.
Your answer must maintain a conversational tone.
You are very very detailed and thorough in your responses.
"""

PROMPT = os.getenv("AITHENA_CHAT_PROMPT", PROMPT_DEFAULT)

MESSAGES = solara.reactive([{"role": "system", "content": PROMPT}])


def add_chunk_to_response(chunk: str):
    """Add chunk to assistant message."""
    MESSAGES.value = [
        *MESSAGES.value[:-1],
        {
            "role": "assistant",
            "content": MESSAGES.value[-1]["content"] + chunk,
        },
    ]


def select_llm(set_llm_name, reset_on_change, set_model_labels, *args):
    """Change the selected LLM."""
    set_llm_name(args[-1])
    if reset_on_change:
        MESSAGES.value = [{"role": "system", "content": PROMPT}]
        set_model_labels({})
        return
    return


CHAT_URL = f"{API_URL}/chat/"


def get_chat_url(model_: str) -> str:
    """Return the chat URL for the given model."""
    return CHAT_URL + model_ + "/generate"


STOP_STREAMING = solara.reactive(False)


@solara.component
def UserQuery(
    messages: solara.Reactive,
    user_query: str,
    set_user_query: Callable,
    llm_name: str,
    task: solara.tasks.Task,
):
    def send_query(*args):
        msg = copy(args[0].v_model)
        set_user_query("")
        messages.value = [*messages.value, {"role": "user", "content": msg}]

    with solara.Row(gap="0px"):

        def manage_click(event, *args):
            if task.pending:
                logger.info("Stop streaming clicked")
                STOP_STREAMING.value = True
                return
            send_query(event, *args)

        def manage_enter(event, *args):
            if user_query == "":
                return
            if task.pending:
                set_user_query(user_query+"\n")
                return
            send_query(event, *args)

        icon = "mdi-send" if not task.pending and user_query != "" else "mdi-stop-circle" if task.pending else "mdi-send; disabled=True;"
        tf = rv.Textarea(
            filled=True,
            rounded=True,
            append_icon=icon,
            label=f"Message {llm_name}",
            autofocus=True,
            v_model=user_query,
            on_v_model=partial(set_user_query),
            auto_grow=True,
            row_height="3px",
            rows="1",
            style_="left: -5px; top: 20px;",
        )
        rv.use_event(
            tf,
            "click:append",
            manage_click,
        )
        rv.use_event(
            tf,
            "keydown.enter.exact.prevent",
            manage_enter,
        )


LLMS_AVAILABLE = requests.get(f"{CHAT_URL}list", timeout=10).json()
DEFAULT_LLM = os.getenv("AITHENA_CHAT_DEFAULT_MODEL", "")

if LLMS_AVAILABLE == []:
    raise ValueError("No LLMs available. Please check the LLM service.")
elif DEFAULT_LLM in LLMS_AVAILABLE:
    DEFAULT_LLM = DEFAULT_LLM 
else:
    DEFAULT_LLM = LLMS_AVAILABLE[0]

CONTEXT_WINDOW_SIZE = os.getenv("AITHENA_CHAT_CONTEXT_WINDOW_SIZE", "2048")

@ solara.component
def Page():

    solara.Style(FILE_PATH.joinpath("style.css"))
    solara.Title("Aithena")

    llm_name, set_llm_name = solara.use_state(DEFAULT_LLM)

    reset_on_change, set_reset_on_change = solara.use_state(False)

    edit_mode, set_edit_mode = solara.use_state(False)

    context_window, set_context = solara.use_state(int(CONTEXT_WINDOW_SIZE))

    user_message_count = len(
        [m for m in MESSAGES.value if m["role"] == "user"])

    is_menu_open, set_is_menu_open = solara.use_state(False)
    model_labels, set_model_labels = solara.use_state({})
    user_query, set_user_query = solara.use_state("")

    edit_index = solara.reactive(None)

    current_edit_value = solara.reactive("")


    def call_llm():
        if user_message_count == 0:
            return
        logger.info(f"Calling LLM with {MESSAGES.value}")
        response = requests.post(
            get_chat_url(llm_name),
            params={"stream": True, "num_ctx": context_window},
            json=MESSAGES.value,
            timeout=120,
            stream=True,
        )
        logger.info(f"Sent messages to LLM: {MESSAGES.value}")
        msgs = [*MESSAGES.value, {"role": "assistant", "content": ""}]
        MESSAGES.value = msgs

        for line in response.iter_lines():
            logger.debug(f"Received line: {line}")
            if not STOP_STREAMING.value:
                if line:
                    add_chunk_to_response(json.loads(line)["delta"])
            else:
                STOP_STREAMING.value = False
                break
        return

    task = solara.lab.use_task(call_llm, dependencies=[
                               user_message_count])  # type: ignore

    with solara.Column(
        style={
            "width": "100%",
            "position": "relative",
            "height": "calc(100vh - 65px)",
            "padding-bottom": "15px",
            "overflow-y": "auto",
        },
    ):
        SelectOptions(
            LLMS_AVAILABLE,
            llm_name,
            set_llm_name,
            set_model_labels,
            select_llm,
            reset_on_change,
            set_reset_on_change,
            MESSAGES.set,
            set_edit_mode,
            context_window,
            set_context,
        )
        with solara.lab.ChatBox():
            for index, item in enumerate(MESSAGES.value):
                is_last = index == len(MESSAGES.value) - 1
                if item["role"] == "system":
                    continue
                if item["role"] == "assistant" and item["content"] == "":
                    continue  # this avoids showing empty assistant messages
                with solara.Column(gap="0px"):
                    with solara.Div(style={"background-color": "rgba(0,0,0.3, 0.06)"}):
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
                            if edit_mode and item["role"] == "assistant":
                                EditableMessage(
                                    MESSAGES,
                                    item["content"],
                                    index,
                                    edit_index,
                                    current_edit_value,
                                )  # add 1 to index to account for prompt
                            else:
                                solara.Markdown(item["content"])
                    if item["role"] == "assistant":
                        ModelLabel(
                            index,
                            llm_name,
                            task,
                            model_labels,
                            set_model_labels,
                            is_menu_open,
                            set_is_menu_open,
                            is_last,
                        )
    with solara.Column(
        style={
            "position": "fixed",
            "bottom": "0",
            "padding-left": "5px",
            "padding-right": "5px",
            "width": "100%",
        },
    ):
        UserQuery(
            MESSAGES,
            user_query,
            set_user_query,
            llm_name,
            task,
        )

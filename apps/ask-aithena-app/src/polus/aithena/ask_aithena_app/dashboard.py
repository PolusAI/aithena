# pylint: disable=E1129, E1120, C0116, C0103, W1203
import json
import os
import re
from copy import copy
from functools import partial
from typing import Callable, Optional

import requests  # type: ignore
import solara
from polus.aithena.common.logger import get_logger
from solara.alias import rv

logger = get_logger(__file__)

__version__ = "0.1.0-dev2"

API_URL = os.getenv("ASK_AITHENA_API_URL", "http://localhost:8080")
logger.info(f"Started Dashboard with Ask Aithena URL: {API_URL}")
ASK_AITHENA_STREAM_ENV = os.getenv("ASK_AITHENA_STREAM", "True")
STREAM = ASK_AITHENA_STREAM_ENV in ["True", "true"]

DATA_SOURCES = [
    "arxiv",
    "biorxiv",
    "chemrxiv",
    "doaj",
    "pubmed",
    "medrxiv",
    "pmc_intros",
    "pmc_methods",
    "pmc_results",
]

MESSAGES: solara.Reactive[list] = solara.reactive([])


@solara.component
def QuestionCounter(n: Optional[int]):
    questions = n or 935
    solara.Info(f"{questions} questions asked!")


@solara.component
def DataSources(
    selected_sources_index, set_selected_sources_index, set_selected_sources_list
):
    def set_selected(*args):
        inds = sorted(args[0])
        set_selected_sources_index(inds)
        set_selected_sources_list([DATA_SOURCES[i] for i in inds])

    with solara.Column():
        solara.Text("Select data sources:")
        chips_ = [
            rv.Chip(
                children=[source],
                filter=True,
                outlined=True,
            )
            for source in DATA_SOURCES
        ]
        rv.ChipGroup(
            children=chips_,
            column=True,
            multiple=True,
            v_model=selected_sources_index,
            on_v_model=set_selected,
        )


@solara.component
def QuestionBox(user_query, set_user_query, messages, set_messages, task):

    def send_query(*args):
        msg = copy(args[0].v_model)
        set_user_query("")
        set_messages([*messages.value, {"role": "user", "content": msg}])

    with solara.Row(
        gap="0px",
    ):
        def manage_click(event, *args):
            send_query(event, *args)

        def manage_enter(event, *args):
            if user_query == "":
                return
            send_query(event, *args)

        tf = rv.Textarea(
            label="Query",
            filled=True,
            rounded=True,
            append_icon=(
                "mdi-send" if not task.pending else "mdi-send; disabled=True;"
            ),
            placeholder="Ask a question, get a response with citations",
            autofocus=True,
            v_model=user_query,
            on_v_model=partial(set_user_query),
            disabled=task.pending,
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


def _md_highlight_links(md: str) -> str:
    """Add link highlights to Markdown."""

    # regular expression to find the URL
    url_pattern = re.compile(r"https?://[^\s]+")

    def replace(match):
        url = match.group(0)
        return f"[{url}]({url})"

    # replace all occurrences of the URL in the text
    return url_pattern.sub(replace, md)


def add_chunk_to_ai_message(messages: list, set_messages: Callable, chunk: str):
    """Add chunk to assistant message."""
    set_messages(
        [
            *messages[:-1],
            {
                "role": "assistant",
                "content": messages[-1]["content"] + chunk,
            },
        ]
    )


@solara.component
def Conversation(
    user_query, set_user_query, messages, set_messages, user_message_count
):
    """Conversation messages, including question box.

    The question box is part of this component so that
    it can be disabled while the task (calling LLM) is running.
    """

    def call_llm():
        if user_message_count == 0:
            return
        user_query_ = messages.value[-1]["content"]
        print(f"Calling LLM with query {user_query_}")
        response = requests.post(
            API_URL + "/ask",
            headers={"Content-Type": "application/json"},
            json={"query": user_query_},
            params={"stream": True},
            stream=True,
            timeout=120,
        )
        print(f"Sent messages to LLM")
        print(response.raise_for_status())
        msgs = [*messages.value, {"role": "assistant", "content": ""}]
        set_messages(msgs)
        for line in response.iter_lines():
            if line:
                add_chunk_to_ai_message(
                    messages.value, set_messages, json.loads(line)["delta"]
                )

    task = solara.lab.use_task(call_llm, dependencies=[
                               user_message_count])  # type: ignore
    loading_label = "Hm...good question...let me think about that..."
    with solara.Column(gap="0px"):

        with solara.Column(
            style={
                "width": "100%",
                "position": "absolute",
                "height": "calc(100vh - 100px)",
                "overflow-y": "auto",
            },
        ):
            if task.pending:
                with solara.Row():
                    rv.ProgressCircular(indeterminate=True, size=25)
                    solara.Text(loading_label)
            with solara.lab.ChatBox():
                for item in messages.value:
                    if item["role"] == "system":
                        continue
                    if item["role"] == "assistant" and item["content"] == "":
                        continue  # this avoids showing empty assistant messages
                    with solara.Column(gap="0px"):
                        with solara.lab.ChatMessage(
                            user=item["role"] == "user",
                            avatar=(
                                "https://api.dicebear.com/5.x/fun-emoji/svg?seed=88"
                                if item["role"] == "user"
                                else "https://files.scb-ncats.io/pyramids/images/robotic_arm_icon_light.png"
                            ),
                            avatar_background_color=None,
                            name=("Aithena" if item["role"]
                                  == "assistant" else "User"),
                            color=(
                                "rgba(0,0,0, 0.06)"
                                if item["role"] == "assistant"
                                else "#ff991f"
                            ),
                            border_radius="20px",
                            style={
                                "padding": "10px",
                            },
                        ):
                            if item["role"] == "user":
                                solara.Markdown(item["content"])
                            else:
                                solara.Markdown(
                                    _md_highlight_links(item["content"]))

            with solara.Column(
                style={
                    "position": "fixed",
                    "bottom": "0",
                    "padding-left": "5px",
                    "padding-right": "5px",
                    "width": "100%",
                },
            ):
                QuestionBox(user_query, set_user_query,
                            messages, set_messages, task)


def _get_user_count(messages):
    if len(messages.value) == 0:  # no messages yet, just initialized
        return 0
    user_message_count = len(
        [m for m in messages.value if m["role"] == "user"])
    return user_message_count


@solara.component
def Page():
    solara.Title("Ask AIthena!")
    solara.Style(
        ".v-application--wrap>div:nth-child(2)>div:nth-child(2) {\n display: none !important;\n}"
    )
    # question_count = requests.get(API_URL + "/questionCount").json()
    # selected_sources_index, set_selected_sources_index = solara.use_state(
    #     list(range(len(DATA_SOURCES)))
    # )
    # selected_sources_list, set_selected_sources_list = solara.use_state(DATA_SOURCES)
    user_query, set_user_query = solara.use_state("")
    # messages, set_messages = solara.use_state([])
    messages, set_messages = MESSAGES, MESSAGES.set
    user_message_count = _get_user_count(messages)
    with solara.Column(style={"padding": "5px"}, gap="0px"):
        # QuestionCounter(question_count)
        # DataSources(
        #     selected_sources_index,
        #     set_selected_sources_index,
        #     set_selected_sources_list,
        # )
        Conversation(
            user_query,
            set_user_query,
            messages,
            set_messages,
            # selected_sources_list,
            user_message_count,
        )

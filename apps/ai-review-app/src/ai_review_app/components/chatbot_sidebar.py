from ai_review_app.models.prompts import PROMPT_CONVERSE
import solara
from functools import partial
from typing import Callable, cast
from chatbot_dash.chatbot_pydantic import ChatBotPydantic
from aithena_services.llms.types import Message
from aithena_services.llms.types.message import Role
from aithena_services.llms.types.base import AithenaLLM

from ai_review_app.models.context import CONTEXT_TAG, Context, Document
import solara
from ai_review_app.utils.common import get_logger
from solara.alias import rv

logger = get_logger(__file__)

@solara.component
def HideSideBarButton(show_sidebar):
    """Hide side bar."""
    def click_btn(*args):
        show_sidebar.value = False

    btn = rv.Btn(
        children=[rv.Icon(children=["mdi-chevron-double-right"], size=38)],
        icon=True,
    )
    rv.use_event(btn, "click", click_btn)



@solara.component
def ShowSideBarButton(show_sidebar):
    """Show side bar."""
    def toggle_show_sidebar(*args):
        show_sidebar.value = not show_sidebar.value

    show_sidebar_button = rv.AppBarNavIcon()
    rv.AppBar(
        children=[rv.Spacer(), show_sidebar_button],
        app=True,
    )
    rv.use_event(show_sidebar_button, "click", toggle_show_sidebar)


@solara.component
def ChatBotTools(
    show_sidebar: solara.Reactive[bool],
    current_llm_name: solara.Reactive[str],
    current_llm: solara.Reactive[AithenaLLM],
    context: solara.Reactive[Context],
    message_history: solara.Reactive[list[Message]]
    ):

    with solara.Row(
        style={"padding-top": "6px", "padding-right": "5px"}, justify="end"
    ):
        btn = HideSideBarButton(show_sidebar)

    def on_response_completed(messages_: solara.Reactive[list[Message]]):
        logger.info(f"@@@@@@@@@@@@@@@ on_response_completed : update context message history")
        message_history.value = messages_.value[1:]

    system_prompt = context.value.to_markdown()
    messages: solara.Reactive[list[Message]] = solara.use_reactive([Message({"role": "system", "content":system_prompt}), *message_history.value])

    logger.info(f"@@@@@@@@@@@@@@@@@@ message_history : {len(message_history.value)}, messages :{len(message_history.value)}")

    ChatBotPydantic(messages, current_llm_name, current_llm, on_response_completed)

@solara.component
def ChatBotSideBar(
    show_sidebar: solara.Reactive[bool],
    current_llm_name,
    current_llm,
    context,
    message_history
):
    """LLM assistant embedded in a side bar."""

    ShowSideBarButton(show_sidebar)

    rv.NavigationDrawer(
        children=[
            ChatBotTools(
                show_sidebar,
                current_llm_name,
                current_llm, 
                context,
                message_history,      
            )
        ],
        # dark=True,
        v_model=show_sidebar.value, #show or hide
        right=True,
        fixed=True,
        floating=True,
        class_="custom-drawer",
        style_="background-color=black;border-radius=10px;padding=20px;",
        width=550.0,
    )

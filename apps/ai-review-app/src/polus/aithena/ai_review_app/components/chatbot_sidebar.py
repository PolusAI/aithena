import solara
from solara.alias import rv
from polus.aithena.ai_review_app.components.chatbot import ChatBot
from polus.aithena.ai_review_app.models.context import Context
from polus.aithena.ai_review_app.utils.common import get_logger

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
    context: solara.Reactive[Context],
    message_history: solara.Reactive[list[dict]]
    ):

    with solara.Row(
        style={"padding-top": "6px", "padding-right": "5px"}, justify="end"
    ):
        btn = HideSideBarButton(show_sidebar)

    def on_response_completed(messages_: solara.Reactive[list[dict]]):
        logger.debug(f"on_response_completed : update current context message history")
        message_history.value = messages_.value[1:]

    system_prompt = context.value.to_markdown()
    messages: solara.Reactive[list[dict]] = solara.use_reactive([{"role": "system", "content":system_prompt}, *message_history.value])

    ChatBot(messages, current_llm_name, on_response_completed)

@solara.component
def ChatBotSideBar(
    show_sidebar: solara.Reactive[bool],
    current_llm_name,
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

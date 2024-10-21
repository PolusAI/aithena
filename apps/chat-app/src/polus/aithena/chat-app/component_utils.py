"""Component utilities for the dashboard."""

# pylint: disable=E1129, E1120, C0116, C0103

from copy import copy
from functools import partial
from typing import Callable

import solara
from solara.alias import rv


@solara.component
def ModelRow(
    llm_options,
    llm_name,
    set_llm_name,
    set_model_labels,
    change_llm_name_,
    reset_on_change,
    set_reset_value,
    messages,
    set_edit_mode_value,
    context_window,
    set_context
):
    with solara.Row(
        style={
            "position": "relative",
            "top": "0",
            "width": "100%",
            "height": "38px",
            "padding-left": "12px",
            "padding-right": "12px",
            "padding-top": "15px",
            # "padding": "5px",
        },
    ):
        auto_complete = rv.Autocomplete(
            label="Model", dense=True, items=llm_options, value=llm_name
        )
        rv.use_event(
            auto_complete,
            "change",
            partial(
                change_llm_name_,
                set_llm_name,
                reset_on_change,
                set_model_labels,
                messages,
            ),
        )
        solara.InputInt(
            label="Context Window",
            value=context_window,
            on_value=set_context,
        )


def update_message(index, edit_index, current_edit_val, messages):
    updated_messages = copy(messages.value)
    updated_messages[index] = {
        "role": "assistant",
        "content": current_edit_val.value,
    }

    messages.value = updated_messages
    edit_index.set(None)


@solara.component
def EditableMessage(messages, message, index, edit_index, current_edit_value):
    def handle_edit():
        edit_index.set(index)
        current_edit_value.set(messages.value[index]["content"])

    if edit_index.value == index:
        solara.MarkdownEditor(
            value=current_edit_value.value, on_value=current_edit_value.set
        )
        solara.Button(
            "SEND",
            on_click=partial(
                update_message, index, edit_index, current_edit_value, messages
            ),
            style={
                "position": "center",
            },
        )
        return

    solara.Markdown(message)
    solara.Button(
        "EDIT",
        on_click=handle_edit,
        style={"position": "center"},
    )
    return


@solara.component
def ModelButton(
    index: int,
    model: str,
    task,
    model_labels: dict,
    set_model_labels: Callable,
    is_last: bool = False,
):
    model_labels_ = copy(model_labels)
    if is_last:
        if not task.pending:
            if index not in model_labels_:
                model_labels_[index] = model
                set_model_labels(model_labels_)
            model_ = model_labels[index] if index in model_labels else model
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
    else:
        if index not in model_labels:
            model_labels_[index] = model
            set_model_labels(model_labels_)
        model_ = model_labels_[index] if index in model_labels_ else model
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
def ChangeModelCard(
    # index: int, model: str,
    change_llm_name: Callable,
    set_is_menu_open: Callable,
    llm_options: list,
):
    def change_llm(*args):
        change_llm_name(*args)
        set_is_menu_open(False)

    with solara.Column(style={"padding": "5px"}):
        solara.Text("Change Model")
        auto_complete = rv.Autocomplete(
            label="Model",
            dense=True,
            items=llm_options,
        )
        rv.use_event(auto_complete, "change", change_llm)


@solara.component
def ModelLabel(
    index: int,
    model: str,
    task,
    model_labels: list,
    set_model_labels: Callable,
    is_menu_open: bool,
    set_is_menu_open: Callable,
    change_llm_name: Callable,
    is_last: bool = False,
):
    if is_last:
        if not task.pending:
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

                    ModelButton(
                        index, model, task, model_labels, set_model_labels, is_last
                    )
                    btn = rv.Btn(
                        children=[
                            rv.Icon(
                                children=["mdi-creation"],
                            )
                        ],
                        icon=True,
                    )
                    with solara.lab.Menu(
                        activator=btn,
                        close_on_content_click=False,
                        open_value=is_menu_open,
                        on_open_value=set_is_menu_open,
                    ):
                        ChangeModelCard(change_llm_name, index, model)
                    # rv.use_event(btn, "click", handle_click)
    else:
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
                ModelButton(index, model, task, model_labels,
                            set_model_labels, is_last)
                rv.Btn(
                    children=[
                        rv.Icon(
                            children=["mdi-creation"],
                        )
                    ],
                    icon=True,
                )

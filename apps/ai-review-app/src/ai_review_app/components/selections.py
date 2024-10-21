"""Selections Components."""

# pylint: disable=C0103, W0106, C0116, W1203, R0913, R0914, R0915, W0613

import time
from functools import partial
from pathlib import Path
from typing import Callable, Optional

import solara
from solara.alias import rv

from ..utils.common import get_logger
from ..models import Selection
from ..config import SELECTIONS_DIR

logger = get_logger(__file__)


@solara.component
def SelectionFromContext(  # pylint: disable=inconsistent-return-statements
    selection: Selection,
    no_title: bool = False,
    set_edit_mode: Optional[Callable] = None,
):
    """Selection from Context Component."""
    if selection == []:
        return
    selected_parts_index, set_selected_parts_index = solara.use_state(
        list(range(len(selection.parts)))
    )
    selected_parts, set_selected_parts = solara.use_state(
        [selection.parts[i] for i in selected_parts_index]
    )

    def update_selected_parts():
        """Update list of Selections based on selected parts."""
        set_selected_parts([selection.parts[i] for i in selected_parts_index])

    solara.use_effect(update_selected_parts, [selected_parts_index])

    error, set_error = solara.use_state(False)
    success, set_success = solara.use_state(False)
    saved_path, set_saved_path = solara.use_state(None)

    selection_name, set_selection_name = solara.use_state(selection.name)

    def update_selection_name():
        """Update selection name."""
        selection.name = selection_name

    solara.use_effect(update_selection_name, [selection_name])

    def save_selection():
        """Save the selection."""
        if selection_name is None:
            logger.error("Tried to save selection without a name")
            set_error(True)
            time.sleep(2)
            set_error(False)
            return
        logger.info("Saving selection")
        sel_to_save = Selection(parts=selected_parts, name=selection_name)
        SELECTIONS_DIR.mkdir(parents=True, exist_ok=True)
        with open(
            SELECTIONS_DIR.joinpath(f"{selection_name}.json"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(sel_to_save.model_dump_json(indent=2))
        set_success(True)
        set_saved_path(
            SELECTIONS_DIR.joinpath(f"{selection_name}.json"),
        )
        time.sleep(4)
        set_success(False)
        if set_edit_mode:
            set_edit_mode(False)

    with solara.Column(gap="5px") as main:
        if not no_title:
            solara.InputText(
                label="Selection Name",
                value=selection_name,
                on_value=set_selection_name,
            )
        chips_ = [
            rv.Chip(
                children=[part.markdown_pretty],
                filter=True,
                outlined=True,
            )
            for part in selection.parts
        ]
        rv.ChipGroup(
            children=chips_,
            column=True,
            multiple=True,
            v_model=selected_parts_index,
            on_v_model=partial(set_selected_parts_index),
        )
        with solara.Row():
            solara.Button(
                label="Save",
                on_click=save_selection,
            )
            if error:
                solara.Error("Please provide a name for the selection")
            if success:
                solara.Success(f"Selection saved successfully to {saved_path}")

    return main


def SelectionLoaded(
    selection: Selection,
    file_name: str,
    call_refresh: Callable,
    set_context_documents_set: Callable,
):
    """Selection loaded from disk Component."""

    edit_mode, set_edit_mode = solara.use_state(False)

    def update_edit(*args):
        set_edit_mode(True)

    def remove_selection(*args):
        """Remove selection from disk."""
        logger.info("Deleting selection {file_name}")
        Path(file_name).unlink()
        call_refresh()

    with solara.Column(gap="5px") as main:
        with solara.Row(
            justify="space-between",
        ):
            solara.Markdown(f"## {selection.name}", style={"padding": "0px"})
            with solara.Row(gap="0px"):
                edit_btn = rv.Btn(
                    children=[rv.Icon(children=["mdi-pencil"])], icon=True
                )
                del_btn = rv.Btn(children=[rv.Icon(children=["mdi-delete"])], icon=True)
                rv.use_event(edit_btn, "click", update_edit)
                rv.use_event(del_btn, "click", remove_selection)

        if edit_mode:
            SelectionFromContext(selection, no_title=True, set_edit_mode=set_edit_mode)
        else:
            chips_ = [
                rv.Chip(
                    children=[part.markdown_pretty],
                    filter=False,
                    outlined=True,
                    column=True,
                )
                for part in selection.parts
            ]
            rv.ChipGroup(children=chips_, column=True)
            solara.Button(
                label="Use Selection",
                on_click=partial(set_context_documents_set, set(selection.parts)),
            ),
    return main


def list_selections():
    """List all selections."""
    return list(SELECTIONS_DIR.glob("*.json"))


@solara.component
def SelectionList(current_selections: solara.Reactive, set_selected: Callable):
    """Component to show/select Selections."""
    selected_index, set_selected_index = solara.use_state(None)
    chips_ = [
        rv.Chip(
            children=[str(sel)],
            filter=True,
            outlined=True,
        )
        for sel in current_selections.value
    ]

    def update_selected_path():
        """Update selected."""
        if selected_index is not None:
            set_selected(str(current_selections.value[selected_index]))

    solara.use_effect(update_selected_path, [selected_index])

    rv.ChipGroup(
        children=chips_,
        multiple=False,
        v_model=selected_index,
        on_v_model=set_selected_index,
        column=True,
    )


@solara.component
def Selections(
    context_documents_set: set,
    set_context_documents_set: Callable,
):
    """Selections Component."""

    selected, set_selected = solara.use_state(None)
    new_selection, set_new_selection = solara.use_state(None)
    current_selections = solara.reactive(list_selections())

    def create_selection_from_context():
        set_new_selection(Selection(parts=list(context_documents_set)))

    def update_selections(*args):
        current_selections.value = list_selections()

    with solara.Column():
        with solara.Card():
            solara.Markdown("# Current Context")
            solara.Button(
                label="Create Selection From Current Context",
                on_click=create_selection_from_context,
                disabled=len(context_documents_set) == 0,
            )
            if new_selection:
                SelectionFromContext(new_selection)

        with solara.Card():
            with solara.Row(gap="2px"):
                solara.Markdown("# Selections")
                ref_btn = rv.Btn(
                    children=[rv.Icon(children=["mdi-refresh"])],
                    icon=True,
                    style_="top: 23px;",
                )
                rv.use_event(ref_btn, "click", update_selections)
            SelectionList(current_selections, set_selected)
            if selected:
                SelectionLoaded(
                    Selection.from_json(selected),
                    selected,
                    update_selections,
                    set_context_documents_set,
                )

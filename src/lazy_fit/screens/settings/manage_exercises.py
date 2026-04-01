"""Manage Exercises — CRUD screen."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import (
    Exercise,
    MuscleGroup,
    get_all_exercises,
    get_all_muscle_groups,
    create_exercise,
    update_exercise,
    delete_exercise,
)


def build(app: toga.App) -> toga.Box:
    list_box_ref: list[Optional[toga.Box]] = [None]

    def _refresh() -> None:
        box = list_box_ref[0]
        if box is None:
            return
        for child in list(box.children):
            box.remove(child)
        _populate(box, app, _refresh)

    def on_add(widget: toga.Widget) -> None:
        _show_form(app, None, _refresh)

    add_btn = toga.Button(t("add"), on_press=on_add, style=Pack(margin=8))

    list_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
    list_box_ref[0] = list_box
    _populate(list_box, app, _refresh)

    scroll = toga.ScrollContainer(content=list_box, style=Pack(flex=1))

    root = toga.Box(
        children=[add_btn, scroll],
        style=Pack(direction=COLUMN, flex=1),
    )
    return root


def _populate(box: toga.Box, app: toga.App, refresh_fn: object) -> None:
    for ex in get_all_exercises():
        _add_row(box, ex, app, refresh_fn)


def _add_row(
    container: toga.Box,
    ex: Exercise,
    app: toga.App,
    refresh_fn: object,
) -> None:
    type_label = t("type_reps") if ex.type == "reps" else t("type_time")
    label = f"{ex.name}  ·  {ex.muscle_group_name}  ({type_label})"

    def on_edit(widget: toga.Widget, ex: Exercise = ex) -> None:
        _show_form(app, ex, refresh_fn)

    def on_delete(widget: toga.Widget, ex: Exercise = ex) -> None:
        delete_exercise(ex.id)
        refresh_fn()

    row = toga.Box(
        children=[
            toga.Label(label, style=Pack(flex=1, margin=4)),
            toga.Button(t("edit"), on_press=on_edit, style=Pack(margin=4)),
            toga.Button(t("delete"), on_press=on_delete, style=Pack(margin=4)),
        ],
        style=Pack(direction=ROW, margin=4),
    )
    container.add(row)


def _show_form(app: toga.App, ex: Optional[Exercise], refresh_fn: object) -> None:
    muscle_groups: list[MuscleGroup] = get_all_muscle_groups()
    mg_names = [mg.name for mg in muscle_groups]

    name_input = toga.TextInput(
        value=ex.name if ex else "",
        placeholder=t("name"),
        style=Pack(flex=1, margin=4),
    )

    current_mg_name = ex.muscle_group_name if ex else (mg_names[0] if mg_names else "")
    mg_select = toga.Selection(
        items=mg_names,
        value=current_mg_name,
        style=Pack(flex=1, margin=4),
    )

    type_options = [t("type_reps"), t("type_time")]
    current_type = t("type_reps") if (not ex or ex.type == "reps") else t("type_time")
    type_select = toga.Selection(
        items=type_options,
        value=current_type,
        style=Pack(flex=1, margin=4),
    )

    error_label = toga.Label("", style=Pack(margin=4, color="red"))

    def on_save(widget: toga.Widget) -> None:
        name = name_input.value.strip()
        if not name:
            error_label.text = t("error_empty_name")
            return

        # Resolve muscle group id
        selected_mg_name = mg_select.value
        mg_id: Optional[int] = None
        for mg in muscle_groups:
            if mg.name == selected_mg_name:
                mg_id = mg.id
                break
        if mg_id is None:
            error_label.text = t("muscle_group") + " ?"
            return

        ex_type = "reps" if type_select.value == t("type_reps") else "time"

        if ex:
            update_exercise(ex.id, name, mg_id, ex_type)
        else:
            create_exercise(name, mg_id, ex_type)

        refresh_fn()
        app.nav_pop()

    def on_cancel(widget: toga.Widget) -> None:
        app.nav_pop()

    form = toga.Box(
        children=[
            toga.Box(
                children=[toga.Label(t("name"), style=Pack(margin=4, width=140)), name_input],
                style=Pack(direction=ROW, margin=4),
            ),
            toga.Box(
                children=[toga.Label(t("muscle_group"), style=Pack(margin=4, width=140)), mg_select],
                style=Pack(direction=ROW, margin=4),
            ),
            toga.Box(
                children=[toga.Label(t("exercise_type"), style=Pack(margin=4, width=140)), type_select],
                style=Pack(direction=ROW, margin=4),
            ),
            error_label,
            toga.Box(
                children=[
                    toga.Button(t("save"), on_press=on_save, style=Pack(margin=8)),
                    toga.Button(t("cancel"), on_press=on_cancel, style=Pack(margin=8)),
                ],
                style=Pack(direction=ROW, margin=8),
            ),
        ],
        style=Pack(direction=COLUMN, margin=16),
    )

    title = t("edit") if ex else t("add")
    app.nav_push(form, f"{title} — {t('manage_exercises')}")

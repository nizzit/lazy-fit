"""Manage Muscle Groups — CRUD screen."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import (
    MuscleGroup,
    get_all_muscle_groups,
    create_muscle_group,
    update_muscle_group,
    delete_muscle_group,
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

    list_box = toga.Box(style=Pack(direction=COLUMN))
    list_box_ref[0] = list_box
    _populate(list_box, app, _refresh)

    scroll_content = toga.Box(
        children=[add_btn, list_box],
        style=Pack(direction=COLUMN),
    )
    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
    root = toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))
    return root


def _populate(box: toga.Box, app: toga.App, refresh_fn: object) -> None:
    for mg in get_all_muscle_groups():
        _add_row(box, mg, app, refresh_fn)


def _add_row(
    container: toga.Box,
    mg: MuscleGroup,
    app: toga.App,
    refresh_fn: object,
) -> None:
    label = mg.name
    if mg.weekly_sets:
        label += f"  ({mg.weekly_sets})"

    def on_edit(widget: toga.Widget, mg: MuscleGroup = mg) -> None:
        _show_form(app, mg, refresh_fn)

    def on_delete(widget: toga.Widget, mg: MuscleGroup = mg) -> None:
        delete_muscle_group(mg.id)
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


def _show_form(app: toga.App, mg: Optional[MuscleGroup], refresh_fn: object) -> None:
    """Push an add/edit form screen."""

    name_input = toga.TextInput(
        value=mg.name if mg else "",
        placeholder=t("name"),
        style=Pack(flex=1, margin=4),
    )
    weekly_input = toga.NumberInput(
        min=0,
        step=1,
        value=mg.weekly_sets if (mg and mg.weekly_sets) else 0,
        style=Pack(flex=1, margin=4),
    )

    error_label = toga.Label("", style=Pack(margin=4, color="red"))

    def on_save(widget: toga.Widget) -> None:
        name = name_input.value.strip()
        if not name:
            error_label.text = t("error_empty_name")
            return
        try:
            ws_raw = weekly_input.value
            ws = int(ws_raw) if ws_raw else None
            if ws == 0:
                ws = None
        except (ValueError, TypeError):
            ws = None

        if mg:
            update_muscle_group(mg.id, name, ws)
        else:
            create_muscle_group(name, ws)

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
                children=[toga.Label(t("weekly_sets"), style=Pack(margin=4, width=140)), weekly_input],
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

    title = t("edit") if mg else t("add")
    app.nav_push(form, f"{title} — {t('manage_muscle_groups')}")

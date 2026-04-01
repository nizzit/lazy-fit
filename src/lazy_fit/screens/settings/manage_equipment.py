"""Manage Equipment — CRUD screen."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import (
    Equipment,
    get_all_equipment,
    create_equipment,
    update_equipment,
    delete_equipment,
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
    for eq in get_all_equipment():
        _add_row(box, eq, app, refresh_fn)


def _add_row(
    container: toga.Box,
    eq: Equipment,
    app: toga.App,
    refresh_fn: object,
) -> None:
    def on_edit(widget: toga.Widget, eq: Equipment = eq) -> None:
        _show_form(app, eq, refresh_fn)

    def on_delete(widget: toga.Widget, eq: Equipment = eq) -> None:
        delete_equipment(eq.id)
        refresh_fn()

    row = toga.Box(
        children=[
            toga.Label(eq.name, style=Pack(flex=1, margin=4)),
            toga.Button(t("edit"), on_press=on_edit, style=Pack(margin=4)),
            toga.Button(t("delete"), on_press=on_delete, style=Pack(margin=4)),
        ],
        style=Pack(direction=ROW, margin=4),
    )
    container.add(row)


def _show_form(app: toga.App, eq: Optional[Equipment], refresh_fn: object) -> None:
    name_input = toga.TextInput(
        value=eq.name if eq else "",
        placeholder=t("name"),
        style=Pack(flex=1, margin=4),
    )
    error_label = toga.Label("", style=Pack(margin=4, color="red"))

    def on_save(widget: toga.Widget) -> None:
        name = name_input.value.strip()
        if not name:
            error_label.text = t("error_empty_name")
            return
        if eq:
            update_equipment(eq.id, name)
        else:
            create_equipment(name)
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

    title = t("edit") if eq else t("add")
    app.nav_push(form, f"{title} — {t('manage_equipment')}")

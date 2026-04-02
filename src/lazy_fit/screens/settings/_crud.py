"""Shared CRUD screen helpers for settings manage-screens."""

from __future__ import annotations

from typing import Callable, Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t


def build_crud_screen(
    app: toga.App,
    populate_fn: Callable[[toga.Box, toga.App, Callable[[], None]], None],
    show_form_fn: Callable[..., None],
) -> toga.Box:
    list_box_ref: list[Optional[toga.Box]] = [None]

    def _refresh() -> None:
        box = list_box_ref[0]
        if box is None:
            return
        for child in list(box.children):
            box.remove(child)
        populate_fn(box, app, _refresh)

    def on_add(widget: toga.Widget) -> None:
        show_form_fn(app, None, _refresh)

    add_btn = toga.Button(t("add"), on_press=on_add, style=Pack(margin=8))

    list_box = toga.Box(style=Pack(direction=COLUMN))
    list_box_ref[0] = list_box
    populate_fn(list_box, app, _refresh)

    scroll_content = toga.Box(
        children=[add_btn, list_box],
        style=Pack(direction=COLUMN),
    )
    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
    return toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))


def build_list_row(name: str, on_edit: Callable, on_delete: Callable) -> toga.Box:
    return toga.Box(
        children=[
            toga.Button(name, on_press=on_edit, style=Pack(flex=1, margin=4)),
            toga.Button(t("delete"), on_press=on_delete, style=Pack(margin=4)),
        ],
        style=Pack(direction=ROW, margin=4),
    )


def build_form_field(label_key: str, widget: toga.Widget) -> toga.Box:
    return toga.Box(
        children=[toga.Label(t(label_key), style=Pack(margin=4, width=140)), widget],
        style=Pack(direction=ROW, margin=4),
    )


def build_entity_form(
    fields: list[toga.Widget],
    error_label: toga.Label,
    on_save: Callable,
    on_cancel: Callable,
    on_delete: Optional[Callable] = None,
) -> toga.Box:
    action_buttons: list[toga.Widget] = [
        toga.Button(t("save"), on_press=on_save, style=Pack(margin=8)),
        toga.Button(t("cancel"), on_press=on_cancel, style=Pack(margin=8)),
    ]
    if on_delete is not None:
        action_buttons.append(
            toga.Button(t("delete"), on_press=on_delete, style=Pack(margin=8))
        )
    return toga.Box(
        children=[
            *fields,
            error_label,
            toga.Box(children=action_buttons, style=Pack(direction=ROW, margin=8)),
        ],
        style=Pack(direction=COLUMN, margin=16),
    )

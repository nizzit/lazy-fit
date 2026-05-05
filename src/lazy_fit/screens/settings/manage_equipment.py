"""Manage Equipment — CRUD screen."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack

from lazy_fit.i18n import t
from lazy_fit.db.models import (
    Equipment,
    get_all_equipment,
    create_equipment,
    update_equipment,
    delete_equipment,
)
from lazy_fit.ui_constants import COLOR_ERROR, themed_pack
from lazy_fit.screens.settings._crud import (
    build_crud_screen,
    build_list_row,
    build_form_field,
    build_entity_form,
)


def build(app: toga.App) -> toga.Box:
    return build_crud_screen(app, _populate, _show_form)


def _populate(box: toga.Box, app: toga.App, refresh_fn: object) -> None:
    for eq in get_all_equipment():

        def on_edit(widget: toga.Widget, eq: Equipment = eq) -> None:
            _show_form(app, eq, refresh_fn)

        box.add(build_list_row(eq.name, on_edit))


def _show_form(app: toga.App, eq: Optional[Equipment], refresh_fn: object) -> None:
    name_input = toga.TextInput(
        value=eq.name if eq else "",
        placeholder=t("name"),
        style=Pack(flex=1, margin=4),
    )
    error_label = toga.Label("", style=themed_pack(margin=4, color=COLOR_ERROR()))

    def on_save(widget: toga.Widget) -> None:
        name = name_input.value.strip()
        if not name:
            error_label.text = t("error_empty_name")
            return
        if eq:
            update_equipment(eq.id, name)
        else:
            create_equipment(name)
        refresh_fn()  # type: ignore[operator]
        app.nav_pop()

    def on_cancel(widget: toga.Widget) -> None:
        app.nav_pop()

    def on_delete(widget: toga.Widget) -> None:
        if eq:
            delete_equipment(eq.id)
            refresh_fn()  # type: ignore[operator]
            app.nav_pop()

    form = build_entity_form(
        [build_form_field("name", name_input)],
        error_label,
        on_save,
        on_cancel,
        on_delete=on_delete if eq else None,
        app=app,
    )
    title = t("edit") if eq else t("add")
    app.nav_push(form, f"{title} — {t('manage_equipment')}")

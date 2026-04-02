"""Manage Muscle Groups — CRUD screen."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack

from lazy_fit.i18n import t
from lazy_fit.db.models import (
    MuscleGroup,
    get_all_muscle_groups,
    create_muscle_group,
    update_muscle_group,
    delete_muscle_group,
)
from lazy_fit.screens.settings._crud import (
    build_crud_screen,
    build_list_row,
    build_form_field,
    build_entity_form,
)


def build(app: toga.App) -> toga.Box:
    return build_crud_screen(app, _populate, _show_form)


def _populate(box: toga.Box, app: toga.App, refresh_fn: object) -> None:
    for mg in get_all_muscle_groups():

        def on_edit(widget: toga.Widget, mg: MuscleGroup = mg) -> None:
            _show_form(app, mg, refresh_fn)

        def on_delete(widget: toga.Widget, mg: MuscleGroup = mg) -> None:
            delete_muscle_group(mg.id)
            refresh_fn()  # type: ignore[operator]

        box.add(build_list_row(mg.name, on_edit, on_delete))


def _show_form(app: toga.App, mg: Optional[MuscleGroup], refresh_fn: object) -> None:
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

        refresh_fn()  # type: ignore[operator]
        app.nav_pop()

    def on_cancel(widget: toga.Widget) -> None:
        app.nav_pop()

    form = build_entity_form(
        [
            build_form_field("name", name_input),
            build_form_field("weekly_sets", weekly_input),
        ],
        error_label,
        on_save,
        on_cancel,
    )
    title = t("edit") if mg else t("add")
    app.nav_push(form, f"{title} — {t('manage_muscle_groups')}")

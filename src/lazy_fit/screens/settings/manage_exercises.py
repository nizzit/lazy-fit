"""Manage Exercises — CRUD screen."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack

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
from lazy_fit.screens.settings._crud import (
    build_crud_screen,
    build_list_row,
    build_form_field,
    build_entity_form,
)


def build(app: toga.App) -> toga.Box:
    return build_crud_screen(app, _populate, _show_form)


def _populate(box: toga.Box, app: toga.App, refresh_fn: object) -> None:
    for ex in get_all_exercises():

        def on_edit(widget: toga.Widget, ex: Exercise = ex) -> None:
            _show_form(app, ex, refresh_fn)

        def on_delete(widget: toga.Widget, ex: Exercise = ex) -> None:
            delete_exercise(ex.id)
            refresh_fn()  # type: ignore[operator]

        box.add(build_list_row(ex.name, on_edit, on_delete))


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

        refresh_fn()  # type: ignore[operator]
        app.nav_pop()

    def on_cancel(widget: toga.Widget) -> None:
        app.nav_pop()

    def on_delete(widget: toga.Widget) -> None:
        if ex:
            delete_exercise(ex.id)
            refresh_fn()  # type: ignore[operator]
            app.nav_pop()

    form = build_entity_form(
        [
            build_form_field("name", name_input),
            build_form_field("muscle_group", mg_select),
            build_form_field("exercise_type", type_select),
        ],
        error_label,
        on_save,
        on_cancel,
        on_delete=on_delete if ex else None,
    )
    title = t("edit") if ex else t("add")
    app.nav_push(form, f"{title} — {t('manage_exercises')}")

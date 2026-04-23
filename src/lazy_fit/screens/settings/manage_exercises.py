"""Manage Exercises — CRUD screen."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.ui_constants import FORM_INPUT_W

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

        box.add(build_list_row(ex.name, on_edit))


def _show_form(
    app: toga.App,
    ex: Optional[Exercise],
    refresh_fn: object,
    preselect_mg_ids: Optional[list[int]] = None,
) -> None:
    muscle_groups: list[MuscleGroup] = get_all_muscle_groups()

    name_input = toga.TextInput(
        value=ex.name if ex else "",
        placeholder=t("name"),
        style=Pack(flex=1, margin=4),
    )

    # Build Switch list for muscle group multi-select
    if ex:
        selected_ids: set[int] = set(ex.muscle_group_ids)
    elif preselect_mg_ids:
        selected_ids = set(preselect_mg_ids)
    else:
        selected_ids = set()
    switches: list[tuple[MuscleGroup, toga.Switch]] = []
    switches_box = toga.Box(style=Pack(direction=COLUMN, margin_left=4))
    for mg in muscle_groups:
        sw = toga.Switch(
            text=mg.name,
            value=mg.id in selected_ids,
            style=Pack(margin=2),
        )
        switches.append((mg, sw))
        switches_box.add(sw)

    type_options = [t("type_reps"), t("type_time")]
    current_type = t("type_reps") if (not ex or ex.type == "reps") else t("type_time")
    type_select = toga.Selection(
        items=type_options,
        value=current_type,
        style=Pack(width=FORM_INPUT_W, margin=4),
    )

    error_label = toga.Label("", style=Pack(margin=4, color="red"))

    def on_save(widget: toga.Widget) -> None:
        name = name_input.value.strip()
        if not name:
            error_label.text = t("error_empty_name")
            return

        mg_ids = [mg.id for mg, sw in switches if sw.value]
        if not mg_ids:
            error_label.text = t("muscle_group") + " ?"
            return

        ex_type = "reps" if type_select.value == t("type_reps") else "time"

        if ex:
            update_exercise(ex.id, name, mg_ids, ex_type)
        else:
            create_exercise(name, mg_ids, ex_type)

        refresh_fn()  # type: ignore[operator]
        app.nav_pop()

    def on_cancel(widget: toga.Widget) -> None:
        app.nav_pop()

    async def on_delete(widget: toga.Widget) -> None:
        if ex:
            result = await app.dialog(
                toga.ConfirmDialog(
                    t("delete"),
                    t("confirm_delete_exercise").format(name=ex.name),
                )
            )
            if result:
                delete_exercise(ex.id)
                refresh_fn()  # type: ignore[operator]
                app.nav_pop()

    mg_label = toga.Label(t("muscle_group"), style=Pack(flex=1, margin=4))
    mg_row = toga.Box(
        children=[mg_label, switches_box],
        style=Pack(direction=ROW, margin=4),
    )

    form = build_entity_form(
        [
            build_form_field("name", name_input),
            mg_row,
            build_form_field("exercise_type", type_select),
        ],
        error_label,
        on_save,
        on_cancel,
        on_delete=on_delete if ex else None,
    )
    title = t("edit") if ex else t("add")
    app.nav_push(form, f"{title} — {t('manage_exercises')}")

"""Manage Muscle Groups — CRUD screen."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.i18n import t
from lazy_fit.widgets import StepperInput
from lazy_fit.db.models import (
    Exercise,
    MuscleGroup,
    get_all_muscle_groups,
    get_exercises_by_muscle_group,
    create_muscle_group,
    update_muscle_group,
    delete_muscle_group,
)
from lazy_fit.ui_constants import COLOR_BTN_ADD, COLOR_ERROR, SPACE_SM, SPACE_XS, themed_pack
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

        box.add(build_list_row(mg.name, on_edit))


def _build_exercises_section(
    app: toga.App, mg: MuscleGroup, refresh_fn: object
) -> toga.Box:
    exercises = get_exercises_by_muscle_group(mg.id)

    def on_add_exercise(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings.manage_exercises import _show_form as _show_exercise_form
        _show_exercise_form(app, None, refresh_fn, preselect_mg_ids=[mg.id])

    section = toga.Box(style=Pack(direction=COLUMN, margin=SPACE_XS))
    section.add(toga.Label(t("exercises"), style=Pack(margin=SPACE_XS)))
    section.add(toga.Button(
        f"+ {t('add')}",
        on_press=on_add_exercise,
        style=themed_pack(margin=SPACE_SM, background_color=COLOR_BTN_ADD()),
    ))

    if not exercises:
        section.add(toga.Label(t("no_exercises_in_group"), style=Pack(margin=4)))
    else:
        for ex in exercises:

            def on_edit_exercise(widget: toga.Widget, ex: Exercise = ex) -> None:
                from lazy_fit.screens.settings.manage_exercises import _show_form as _show_exercise_form
                _show_exercise_form(app, ex, refresh_fn)

            section.add(build_list_row(ex.name, on_edit_exercise))

    return section


def _show_form(app: toga.App, mg: Optional[MuscleGroup], refresh_fn: object) -> None:
    name_input = toga.TextInput(
        value=mg.name if mg else "",
        placeholder=t("name"),
        style=Pack(flex=1, margin=4),
    )
    weekly_input = StepperInput(
        min=0,
        step=1,
        value=mg.weekly_sets if (mg and mg.weekly_sets) else 0,
        style=Pack(margin=4),
    )
    rest_days_input = StepperInput(
        min=0,
        step=1,
        value=mg.rest_days if (mg and mg.rest_days is not None) else 0,
        style=Pack(margin=4),
    )
    error_label = toga.Label("", style=themed_pack(margin=4, color=COLOR_ERROR()))

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
        try:
            rd_raw = rest_days_input.value
            rd = int(rd_raw) if rd_raw else None
            if rd == 0:
                rd = None
        except (ValueError, TypeError):
            rd = None

        if mg:
            update_muscle_group(mg.id, name, ws, rd)
        else:
            create_muscle_group(name, ws, rd)

        refresh_fn()  # type: ignore[operator]
        app.nav_pop()

    def on_cancel(widget: toga.Widget) -> None:
        app.nav_pop()

    def on_delete(widget: toga.Widget) -> None:
        if mg:
            delete_muscle_group(mg.id)
            refresh_fn()  # type: ignore[operator]
            app.nav_pop()

    fields: list[toga.Widget] = [
        build_form_field("name", name_input),
        build_form_field("weekly_sets", weekly_input),
        build_form_field("rest_days_override_label", rest_days_input),
    ]
    if mg:
        fields.append(_build_exercises_section(app, mg, refresh_fn))

    form = build_entity_form(
        fields,
        error_label,
        on_save,
        on_cancel,
        on_delete=on_delete if mg else None,
        app=app,
    )
    title = t("edit") if mg else t("add")
    app.nav_push(form, f"{title} — {t('manage_muscle_groups')}")

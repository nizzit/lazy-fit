"""Log Set screen — record a set + show today's workout summary."""

from __future__ import annotations

import datetime
from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.widgets import StepperInput
from lazy_fit.screens._workout_log import populate_workout_log
from lazy_fit.db.models import (
    Exercise,
    get_all_equipment,
    create_workout_set,
    get_last_value_for_exercise,
    get_last_equipment_for_exercise,
)


def _today() -> str:
    return datetime.date.today().isoformat()


def build(app: toga.App, exercise: Exercise) -> toga.Box:
    """Build and return the log-set screen for *exercise*."""

    today = _today()
    equipment_list = get_all_equipment()
    last_value = get_last_value_for_exercise(exercise.id)
    last_equipment_id = get_last_equipment_for_exercise(exercise.id)

    # ------------------------------------------------------------------ refs
    value_input_ref: list[Optional[toga.NumberInput]] = [None]
    equip_select_ref: list[Optional[toga.Selection]] = [None]
    history_box_ref: list[Optional[toga.Box]] = [None]

    # ------------------------------------------------------------------ exercise timer
    def _on_exercise_timer_done(elapsed_secs: int) -> None:
        if value_input_ref[0] is not None:
            value_input_ref[0].value = elapsed_secs

    def on_start_timer(widget: toga.Widget) -> None:
        from lazy_fit.screens.timer import build as build_timer

        app.nav_push(
            build_timer(
                app,
                mode="stopwatch",
                on_done=_on_exercise_timer_done,
                stop_label=t("timer_stop"),
                header=exercise.name,
            ),
            t("timer"),
        )

    # ------------------------------------------------------------------ rest timer
    def _start_rest_timer() -> None:
        from lazy_fit.db.models import get_setting
        from lazy_fit.screens.timer import build as build_timer

        if get_setting("rest_timer_enabled", "0") != "1":
            return
        try:
            secs = int(get_setting("rest_timer_seconds", "60"))
        except ValueError:
            secs = 60
        if secs <= 0:
            return

        app.nav_push(
            build_timer(
                app,
                mode="countdown",
                on_done=lambda: None,
                stop_label=t("rest_timer_skip"),
                initial_secs=secs,
                header=t("rest_timer"),
            ),
            t("rest_timer"),
        )

    # ------------------------------------------------------------------ save
    def on_save(widget: toga.Widget) -> None:
        raw_value = value_input_ref[0].value if value_input_ref[0] else None
        try:
            int_value = int(raw_value) if raw_value is not None else 0
        except (ValueError, TypeError):
            int_value = 0

        eq_id: Optional[int] = None
        if equip_select_ref[0] and equip_select_ref[0].value:
            sel = equip_select_ref[0].value
            if sel != t("no_equipment"):
                for eq in equipment_list:
                    if eq.name == sel:
                        eq_id = eq.id
                        break

        if exercise.type == "reps":
            create_workout_set(today, exercise.id, reps=int_value, equipment_id=eq_id)
        else:
            create_workout_set(today, exercise.id, duration_sec=int_value, equipment_id=eq_id)

        if value_input_ref[0]:
            value_input_ref[0].value = int_value

        _refresh_history()
        _start_rest_timer()

    # ------------------------------------------------------------------ history
    def _refresh_history() -> None:
        box = history_box_ref[0]
        if box is None:
            return
        for child in list(box.children):
            box.remove(child)
        populate_workout_log(box, today, app, _refresh_history, reverse=True)

    # ------------------------------------------------------------------ build UI
    header = toga.Label(
        f"{exercise.name}  ·  {exercise.muscle_group_name}",
        style=Pack(margin=8, font_size=16),
    )

    value_input = StepperInput(
        min=0,
        step=1,
        value=last_value if last_value is not None else 0,
        style=Pack(flex=1, margin=4),
    )
    value_input_ref[0] = value_input

    if exercise.type == "reps":
        input_label = toga.Label(t("reps"), style=Pack(margin=4, width=120))
        input_row = toga.Box(
            children=[input_label, value_input],
            style=Pack(direction=ROW, margin=4),
        )
        form_children: list[toga.Widget] = [input_row]
    else:
        start_btn = toga.Button(
            t("timer_start"),
            on_press=on_start_timer,
            style=Pack(margin=4),
        )
        input_label = toga.Label(t("duration"), style=Pack(margin=4, width=120))
        input_row = toga.Box(
            children=[input_label, value_input],
            style=Pack(direction=ROW, margin=4),
        )
        form_children = [start_btn, input_row]

    equip_options = [t("no_equipment")] + [eq.name for eq in equipment_list]
    _last_equip_name = next(
        (eq.name for eq in equipment_list if eq.id == last_equipment_id), None
    )
    equip_select = toga.Selection(
        items=equip_options,
        value=_last_equip_name if _last_equip_name is not None else t("no_equipment"),
        style=Pack(flex=1, margin=4),
    )
    equip_select_ref[0] = equip_select

    equip_row = toga.Box(
        children=[
            toga.Label(t("equipment"), style=Pack(margin=4, width=120)),
            equip_select,
        ],
        style=Pack(direction=ROW, margin=4),
    )

    save_btn = toga.Button(t("save_set"), on_press=on_save, style=Pack(margin=12))

    form_box = toga.Box(
        children=form_children + [equip_row, save_btn],
        style=Pack(direction=COLUMN, margin=8),
    )

    history_title = toga.Label(
        t("todays_workout"),
        style=Pack(margin=(12, 8, 4, 8), font_size=14),
    )
    history_box = toga.Box(style=Pack(direction=COLUMN))
    history_box_ref[0] = history_box
    populate_workout_log(history_box, today, app, _refresh_history, reverse=True)

    scroll_content = toga.Box(
        children=[header, form_box, history_title, history_box],
        style=Pack(direction=COLUMN),
    )
    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
    return toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))

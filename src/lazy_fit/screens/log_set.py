"""Log Set screen — record a set + show today's workout summary."""

from __future__ import annotations

import datetime
from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.ui_constants import COLOR_BTN_ADD, COLOR_BTN_PRIMARY, FONT_LG, FONT_MD, FORM_INPUT_W, SPACE_SM, SPACE_XS, themed_pack
from lazy_fit.widgets import StepperInput
from lazy_fit.screens._workout_log import populate_workout_log
from lazy_fit.db.models import (
    Exercise,
    get_all_equipment,
    create_workout_set,
    get_default_value_for_next_set,
    get_last_equipment_for_exercise,
)


def _today() -> str:
    return datetime.date.today().isoformat()


def build(app: toga.App, exercise: Exercise) -> toga.Box:
    """Build and return the log-set screen for *exercise*."""

    today = _today()
    equipment_list = get_all_equipment()
    last_equipment_id = get_last_equipment_for_exercise(exercise.id)

    def _selected_equipment_id() -> Optional[int]:
        """Return the equipment_id currently selected in equip_select, or None."""
        sel_widget = equip_select_ref[0]
        if not sel_widget or not sel_widget.value:
            return None
        sel = sel_widget.value
        if sel == t("no_equipment"):
            return None
        for eq in equipment_list:
            if eq.name == sel:
                return eq.id
        return None

    def _default_value() -> int:
        eq_id = _selected_equipment_id()
        # filter_by_equipment=True only when equip_select has been initialised
        # (avoids filtering on first call before the widget exists)
        use_filter = equip_select_ref[0] is not None
        val = get_default_value_for_next_set(
            exercise.id, today, equipment_id=eq_id, filter_by_equipment=use_filter
        )
        return val if val is not None else 0

    # ------------------------------------------------------------------ refs
    value_input_ref: list[Optional[StepperInput]] = [None]
    equip_select_ref: list[Optional[toga.Selection]] = [None]
    history_box_ref: list[Optional[toga.Box]] = [None]
    timer_done_ref: list[bool] = [False]
    action_btn_ref: list[Optional[toga.Button]] = [None]

    # ------------------------------------------------------------------ exercise timer
    def _set_btn_start_mode() -> None:
        btn = action_btn_ref[0]
        if btn is None:
            return
        btn.text = t("timer_start")
        btn.on_press = on_start_timer
        if COLOR_BTN_PRIMARY() is not None:
            btn.style.background_color = COLOR_BTN_PRIMARY()

    def _set_btn_save_mode() -> None:
        btn = action_btn_ref[0]
        if btn is None:
            return
        btn.text = t("save_set")
        btn.on_press = on_save
        if COLOR_BTN_ADD() is not None:
            btn.style.background_color = COLOR_BTN_ADD()

    def _on_exercise_timer_done(elapsed_secs: int) -> None:
        if value_input_ref[0] is not None:
            value_input_ref[0].value = elapsed_secs
        timer_done_ref[0] = True
        _set_btn_save_mode()

    def on_start_timer(widget: toga.Widget) -> None:
        from lazy_fit.screens.timer import build as build_timer

        build_timer(
            app,
            mode="stopwatch",
            on_done=_on_exercise_timer_done,
            stop_label=t("timer_stop"),
            header=exercise.name,
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

        build_timer(
            app,
            mode="countdown",
            on_done=lambda: None,
            stop_label=t("rest_timer_skip"),
            initial_secs=secs,
            header=t("rest_timer"),
        )

    # ------------------------------------------------------------------ save
    def on_save(widget: toga.Widget) -> None:
        # Cancel any running countdown (rest timer) before saving a new set.
        if (
            getattr(app, "active_timer", None)
            and app.active_timer.get("mode") == "countdown"
        ):
            app.cancel_active_timer()
            app._render_current()
        raw_value = value_input_ref[0].value if value_input_ref[0] else None
        try:
            int_value = int(raw_value) if raw_value is not None else 0
        except (ValueError, TypeError):
            int_value = 0

        eq_id = _selected_equipment_id()

        if exercise.type == "reps":
            create_workout_set(today, exercise.id, reps=int_value, equipment_id=eq_id)
        else:  # time
            create_workout_set(
                today, exercise.id, duration_sec=int_value, equipment_id=eq_id
            )

        # Reset timer gate for time exercises
        if exercise.type == "time":
            timer_done_ref[0] = False
            _set_btn_start_mode()

        if value_input_ref[0]:
            value_input_ref[0].value = _default_value()

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
        f"{exercise.name}  ·  {', '.join(exercise.muscle_group_names)}",
        style=Pack(margin=SPACE_SM, font_size=FONT_LG),
    )

    value_input = StepperInput(
        min=0,
        step=1,
        value=_default_value(),
        style=Pack(margin=4),
    )
    value_input_ref[0] = value_input

    def _field(label_key: str, widget: toga.Widget) -> toga.Box:
        return toga.Box(
            children=[
                toga.Label(t(label_key), style=Pack(margin=SPACE_XS)),
                toga.Box(children=[toga.Box(style=Pack(flex=1)), widget], style=Pack(direction=ROW)),
            ],
            style=Pack(direction=COLUMN, margin=SPACE_XS),
        )

    if exercise.type == "reps":
        form_children: list[toga.Widget] = [_field("reps", value_input)]
    else:  # time
        action_btn = toga.Button(
            t("timer_start"),
            on_press=on_start_timer,
            style=themed_pack(flex=1, margin=SPACE_SM, background_color=COLOR_BTN_PRIMARY()),
        )
        action_btn_ref[0] = action_btn
        form_children = [_field("duration", value_input)]

    equip_options = [t("no_equipment")] + [eq.name for eq in equipment_list]
    _last_equip_name = next(
        (eq.name for eq in equipment_list if eq.id == last_equipment_id), None
    )
    def on_equipment_change(widget: toga.Widget) -> None:
        if value_input_ref[0] is not None:
            value_input_ref[0].value = _default_value()

    equip_select = toga.Selection(
        items=equip_options,
        value=_last_equip_name if _last_equip_name is not None else t("no_equipment"),
        on_change=on_equipment_change,
        style=Pack(width=FORM_INPUT_W, margin=4),
    )
    equip_select_ref[0] = equip_select

    equip_row = toga.Box(
        children=[
            toga.Label(t("equipment"), style=Pack(margin=SPACE_XS)),
            toga.Box(children=[toga.Box(style=Pack(flex=1)), equip_select], style=Pack(direction=ROW)),
        ],
        style=Pack(direction=COLUMN, margin=SPACE_XS),
    )

    save_btn = toga.Button(t("save_set"), on_press=on_save, style=themed_pack(flex=1, margin=SPACE_SM, background_color=COLOR_BTN_ADD()))

    bottom_btn = save_btn if exercise.type == "reps" else action_btn

    form_box = toga.Box(
        children=form_children + [equip_row, bottom_btn],
        style=Pack(direction=COLUMN, margin=8),
    )

    history_title = toga.Label(
        t("todays_workout"),
        style=Pack(margin=SPACE_SM, font_size=FONT_MD),
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

"""Edit Set screen — modify an existing workout set."""

from __future__ import annotations

from typing import Callable

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.ui_constants import SPACE_MD, SPACE_SM, SPACE_XS, COLOR_BTN_PRIMARY, COLOR_BTN_SECONDARY, COLOR_BTN_DANGER, themed_pack
from lazy_fit.widgets import StepperInput, ConfirmButton
from lazy_fit.db.models import WorkoutSet, Equipment, update_workout_set, delete_workout_set, get_equipment_ids_for_set
from lazy_fit.screens.settings._crud import wrap_scroll
from lazy_fit.screens._equipment_picker import build_equipment_picker


def build(
    app: toga.App,
    ws: WorkoutSet,
    equipment_list: list[Equipment],
    on_saved: Callable[[], None],
) -> toga.Box:
    """Build and return the edit-set screen."""

    # Value input
    if ws.exercise_type == "reps":
        initial_value = ws.reps or 0
    else:
        initial_value = ws.duration_sec or 0
    value_input = StepperInput(
        min=0,
        step=1,
        value=initial_value,
        style=Pack(margin=SPACE_XS),
    )

    label_key = "reps" if ws.exercise_type == "reps" else "duration"
    def _field(lk: str, widget: toga.Widget) -> toga.Box:
        return toga.Box(
            children=[
                toga.Label(t(lk), style=Pack(margin=SPACE_XS)),
                toga.Box(children=[toga.Box(style=Pack(flex=1)), widget], style=Pack(direction=ROW)),
            ],
            style=Pack(direction=COLUMN, margin=SPACE_XS),
        )

    input_row = _field(label_key, value_input)

    # Multi-select equipment picker
    current_eq_ids: list[int] = get_equipment_ids_for_set(ws.id)
    selected_eq_ids_ref: list[list[int]] = [list(current_eq_ids)]

    def _on_equipment_change(ids: list[int]) -> None:
        selected_eq_ids_ref[0] = ids

    equip_picker = build_equipment_picker(
        equipment_list,
        initial_ids=list(current_eq_ids),
        on_change=_on_equipment_change,
        app=app,
    )

    equip_row = toga.Box(
        children=[
            toga.Label(t("equipment"), style=Pack(margin=SPACE_XS)),
            equip_picker,
        ],
        style=Pack(direction=COLUMN, margin=SPACE_XS),
    )

    def on_save(widget: toga.Widget) -> None:
        raw_value = value_input.value
        try:
            int_value = int(raw_value) if raw_value is not None else 0
        except (ValueError, TypeError):
            int_value = 0

        eq_ids = selected_eq_ids_ref[0]

        if ws.exercise_type == "reps":
            update_workout_set(ws.id, reps=int_value, equipment_ids=eq_ids)
        else:  # time
            update_workout_set(ws.id, duration_sec=int_value, equipment_ids=eq_ids)

        on_saved()
        app.nav_pop()

    def on_cancel(widget: toga.Widget) -> None:
        app.nav_pop()

    def on_delete(widget: toga.Widget) -> None:
        delete_workout_set(ws.id)
        on_saved()
        app.nav_pop()

    save_btn = toga.Button(t("save"), on_press=on_save, style=themed_pack(flex=1, margin=SPACE_SM, background_color=COLOR_BTN_PRIMARY()))
    cancel_btn = toga.Button(t("cancel"), on_press=on_cancel, style=themed_pack(flex=1, margin=SPACE_SM, background_color=COLOR_BTN_SECONDARY()))
    delete_btn = ConfirmButton(t("delete"), on_delete, app, margin=SPACE_SM, background_color=COLOR_BTN_DANGER())

    btn_row = toga.Box(
        children=[save_btn, cancel_btn, delete_btn],
        style=Pack(direction=ROW, margin=SPACE_SM),
    )

    root = toga.Box(
        children=[input_row, equip_row, btn_row],
        style=Pack(direction=COLUMN, margin=SPACE_MD),
    )
    return wrap_scroll(root)

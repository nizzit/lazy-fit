"""Edit Set screen — modify an existing workout set."""

from __future__ import annotations

from typing import Optional, Callable

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import WorkoutSet, Equipment, update_workout_set


def build(
    app: toga.App,
    ws: WorkoutSet,
    equipment_list: list[Equipment],
    on_saved: Callable[[], None],
) -> toga.Box:
    """Build and return the edit-set screen."""

    # Value input
    initial_value = ws.reps if ws.exercise_type == "reps" else (ws.duration_sec or 0)
    value_input = toga.NumberInput(
        min=0,
        step=1,
        value=initial_value,
        style=Pack(flex=1, margin=4),
    )

    label_key = "reps" if ws.exercise_type == "reps" else "duration"
    input_row = toga.Box(
        children=[
            toga.Label(t(label_key), style=Pack(margin=4, width=120)),
            value_input,
        ],
        style=Pack(direction=ROW, margin=4),
    )

    # Equipment picker
    equip_options = [t("no_equipment")] + [eq.name for eq in equipment_list]
    current_equip = ws.equipment_name if ws.equipment_name else t("no_equipment")
    equip_select = toga.Selection(
        items=equip_options,
        value=current_equip,
        style=Pack(flex=1, margin=4),
    )
    equip_row = toga.Box(
        children=[
            toga.Label(t("equipment"), style=Pack(margin=4, width=120)),
            equip_select,
        ],
        style=Pack(direction=ROW, margin=4),
    )

    def on_save(widget: toga.Widget) -> None:
        raw_value = value_input.value
        try:
            int_value = int(raw_value) if raw_value is not None else 0
        except (ValueError, TypeError):
            int_value = 0

        eq_id: Optional[int] = None
        sel = equip_select.value
        if sel and sel != t("no_equipment"):
            for eq in equipment_list:
                if eq.name == sel:
                    eq_id = eq.id
                    break

        if ws.exercise_type == "reps":
            update_workout_set(ws.id, reps=int_value, equipment_id=eq_id)
        else:
            update_workout_set(ws.id, duration_sec=int_value, equipment_id=eq_id)

        on_saved()
        app.nav_pop()

    def on_cancel(widget: toga.Widget) -> None:
        app.nav_pop()

    save_btn = toga.Button(t("save"), on_press=on_save, style=Pack(margin=8))
    cancel_btn = toga.Button(t("cancel"), on_press=on_cancel, style=Pack(margin=8))

    btn_row = toga.Box(
        children=[save_btn, cancel_btn],
        style=Pack(direction=ROW, margin=8),
    )

    root = toga.Box(
        children=[input_row, equip_row, btn_row],
        style=Pack(direction=COLUMN, margin=16),
    )
    return root

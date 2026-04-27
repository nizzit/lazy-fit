"""Edit Set screen — modify an existing workout set."""

from __future__ import annotations

from typing import Optional, Callable

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.ui_constants import FORM_INPUT_W, SPACE_MD, SPACE_SM, SPACE_XS, COLOR_BTN_PRIMARY, COLOR_BTN_SECONDARY, COLOR_BTN_DANGER
from lazy_fit.widgets import StepperInput
from lazy_fit.db.models import WorkoutSet, Equipment, update_workout_set, delete_workout_set
from lazy_fit.screens.settings._crud import wrap_scroll


def build(
    app: toga.App,
    ws: WorkoutSet,
    equipment_list: list[Equipment],
    on_saved: Callable[[], None],
) -> toga.Box:
    """Build and return the edit-set screen."""

    # Value input
    initial_value = ws.reps if ws.exercise_type == "reps" else (ws.duration_sec or 0)
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

    # Equipment picker
    equip_options = [t("no_equipment")] + [eq.name for eq in equipment_list]
    current_equip = ws.equipment_name if ws.equipment_name else t("no_equipment")
    equip_select = toga.Selection(
        items=equip_options,
        value=current_equip,
        style=Pack(width=FORM_INPUT_W, margin=SPACE_XS),
    )
    equip_row = _field("equipment", equip_select)

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

    async def on_delete(widget: toga.Widget) -> None:
        result = await app.dialog(toga.ConfirmDialog(t("delete"), t("confirm_delete_set")))
        if result:
            delete_workout_set(ws.id)
            on_saved()
            app.nav_pop()

    save_btn = toga.Button(t("save"), on_press=on_save, style=Pack(flex=1, margin=SPACE_SM, background_color=COLOR_BTN_PRIMARY))
    cancel_btn = toga.Button(t("cancel"), on_press=on_cancel, style=Pack(flex=1, margin=SPACE_SM, background_color=COLOR_BTN_SECONDARY))
    delete_btn = toga.Button(t("delete"), on_press=on_delete, style=Pack(margin=SPACE_SM, background_color=COLOR_BTN_DANGER))

    btn_row = toga.Box(
        children=[save_btn, cancel_btn, delete_btn],
        style=Pack(direction=ROW, margin=SPACE_SM),
    )

    root = toga.Box(
        children=[input_row, equip_row, btn_row],
        style=Pack(direction=COLUMN, margin=SPACE_MD),
    )
    return wrap_scroll(root)

"""Workout Detail screen — view and edit a single workout by date."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.ui_constants import COLOR_BTN_PRIMARY, COLOR_BTN_DANGER, COLOR_DIFF_DOWN, COLOR_DIFF_UP, FONT_MD, SPACE_SM, SPACE_XS, themed_pack
from lazy_fit.db.models import (
    WorkoutSet,
    get_sets_for_date,
    get_all_equipment,
    update_workout_set,
    delete_workout_set,
    delete_workout_by_date,
    get_prev_workout_values_for_exercise,
)


def build(app: toga.App, date: str) -> toga.Box:
    """Build and return the workout detail screen for *date*."""

    equipment_list = get_all_equipment()
    content_box_ref: list[Optional[toga.Box]] = [None]

    def _refresh() -> None:
        box = content_box_ref[0]
        if box is None:
            return
        for child in list(box.children):
            box.remove(child)
        _populate(box, date, equipment_list, app, _refresh)

    async def on_delete_workout(widget: toga.Widget) -> None:
        result = await app.dialog(
            toga.ConfirmDialog(
                t("delete_workout"),
                t("confirm_delete_workout").format(date=date),
            )
        )
        if result:
            delete_workout_by_date(date)
            app.nav_pop()

    delete_btn = toga.Button(
        t("delete_workout"),
        on_press=on_delete_workout,
        style=themed_pack(margin=8, background_color=COLOR_BTN_DANGER()),
    )

    content_box = toga.Box(style=Pack(direction=COLUMN))
    content_box_ref[0] = content_box
    _populate(content_box, date, equipment_list, app, _refresh)

    scroll_content = toga.Box(
        children=[delete_btn, content_box],
        style=Pack(direction=COLUMN),
    )
    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
    root = toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))
    return root


def _populate(
    box: toga.Box,
    date: str,
    equipment_list: list,
    app: toga.App,
    refresh_fn: object,
) -> None:
    sets = get_sets_for_date(date)

    if not sets:
        box.add(toga.Label(t("no_sets_today"), style=Pack(margin=8)))
        return

    # Group by exercise
    groups: dict[str, list[WorkoutSet]] = {}
    for s in sets:
        groups.setdefault(s.exercise_name, []).append(s)

    for ex_name, ex_sets in groups.items():
        box.add(toga.Label(ex_name, style=Pack(margin=SPACE_SM, font_size=FONT_MD)))
        prev_values = get_prev_workout_values_for_exercise(ex_sets[0].exercise_id, date)
        for i, ws in enumerate(ex_sets):
            _add_set_row(box, ws, i, prev_values, equipment_list, app, refresh_fn)


def _add_set_row(
    container: toga.Box,
    ws: WorkoutSet,
    set_index: int,
    prev_values: list[int],
    equipment_list: list,
    app: toga.App,
    refresh_fn: object,
) -> None:
    if ws.exercise_type == "reps":
        current_val = ws.reps or 0
        value_text = t("set_reps_label").format(reps=ws.reps)
    else:
        current_val = ws.duration_sec or 0
        secs = current_val
        value_text = t("set_time_label").format(mm=f"{secs // 60:02d}", ss=f"{secs % 60:02d}")

    if ws.equipment_name:
        value_text += f"  [{ws.equipment_name}]"

    # Diff vs previous workout
    label_color: Optional[str] = None
    if set_index < len(prev_values):
        diff = current_val - prev_values[set_index]
        if diff > 0:
            value_text += f"  +{diff}"
            label_color = COLOR_DIFF_UP()
        elif diff < 0:
            value_text += f"  {diff}"
            label_color = COLOR_DIFF_DOWN()
        else:
            value_text += "  ="

    label_style = Pack(flex=1, margin=SPACE_XS)
    if label_color is not None:
        label_style = Pack(flex=1, margin=SPACE_XS, color=label_color)

    async def on_delete(widget: toga.Widget, ws: WorkoutSet = ws) -> None:
        result = await app.dialog(
            toga.ConfirmDialog(t("delete"), t("confirm_delete_set"))
        )
        if result:
            delete_workout_set(ws.id)
            refresh_fn()

    def on_edit(widget: toga.Widget, ws: WorkoutSet = ws) -> None:
        from lazy_fit.screens.edit_set import build as build_edit
        app.nav_push(
            build_edit(app, ws, equipment_list, refresh_fn),
            t("edit_set"),
        )

    row = toga.Box(
        children=[
            toga.Label(value_text, style=label_style),
            toga.Button(t("edit_set"), on_press=on_edit, style=themed_pack(margin=SPACE_XS, background_color=COLOR_BTN_PRIMARY())),
            toga.Button(t("delete"), on_press=on_delete, style=themed_pack(margin=SPACE_XS, background_color=COLOR_BTN_DANGER())),
        ],
        style=Pack(direction=ROW, margin=SPACE_XS),
    )
    container.add(row)

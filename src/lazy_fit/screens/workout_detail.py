"""Workout Detail screen — view and edit a single workout by date."""

from __future__ import annotations

from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import (
    WorkoutSet,
    get_sets_for_date,
    get_all_equipment,
    update_workout_set,
    delete_workout_set,
    delete_workout_by_date,
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

    def on_delete_workout(widget: toga.Widget) -> None:
        async def _confirm(app: toga.App, **kwargs: object) -> None:
            result = await app.dialog(
                toga.ConfirmDialog(
                    t("delete_workout"),
                    t("confirm_delete_workout").format(date=date),
                )
            )
            if result:
                delete_workout_by_date(date)
                app.nav_pop()

        app.add_background_task(_confirm)

    delete_btn = toga.Button(
        t("delete_workout"),
        on_press=on_delete_workout,
        style=Pack(margin=8),
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
        box.add(toga.Label(ex_name, style=Pack(margin=(8, 8, 2, 8), font_size=14)))
        for ws in ex_sets:
            _add_set_row(box, ws, equipment_list, app, refresh_fn)


def _add_set_row(
    container: toga.Box,
    ws: WorkoutSet,
    equipment_list: list,
    app: toga.App,
    refresh_fn: object,
) -> None:
    if ws.exercise_type == "reps":
        value_text = t("set_reps_label").format(reps=ws.reps)
    else:
        secs = ws.duration_sec or 0
        value_text = t("set_time_label").format(mm=f"{secs // 60:02d}", ss=f"{secs % 60:02d}")

    if ws.equipment_name:
        value_text += f"  [{ws.equipment_name}]"

    def on_delete(widget: toga.Widget, ws: WorkoutSet = ws) -> None:
        async def _confirm(app: toga.App, **kwargs: object) -> None:
            result = await app.dialog(
                toga.ConfirmDialog(t("delete"), t("confirm_delete_set"))
            )
            if result:
                delete_workout_set(ws.id)
                refresh_fn()

        app.add_background_task(_confirm)

    def on_edit(widget: toga.Widget, ws: WorkoutSet = ws) -> None:
        from lazy_fit.screens.edit_set import build as build_edit
        app.nav_push(
            build_edit(app, ws, equipment_list, refresh_fn),
            t("edit_set"),
        )

    row = toga.Box(
        children=[
            toga.Label(value_text, style=Pack(flex=1, margin=4)),
            toga.Button(t("edit_set"), on_press=on_edit, style=Pack(margin=4)),
            toga.Button(t("delete"), on_press=on_delete, style=Pack(margin=4)),
        ],
        style=Pack(direction=ROW, margin=(2, 8)),
    )
    container.add(row)

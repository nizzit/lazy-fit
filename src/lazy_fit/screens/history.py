"""Workout History screen — list of past workouts with inline details."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.ui_constants import COLOR_BTN_DANGER, FONT_MD, FONT_SM, SPACE_SM, themed_pack
from lazy_fit.db.models import get_workout_dates, delete_workout_by_date, get_muscle_group_names_for_date
from lazy_fit.screens._workout_log import populate_workout_log

_BATCH_SIZE = 5


def build(app: toga.App) -> toga.Box:
    """Build and return the history screen."""

    scroll_content_ref: list[Optional[toga.Box]] = [None]

    def _rebuild() -> None:
        box = scroll_content_ref[0]
        if box is None:
            return
        for child in list(box.children):
            box.remove(child)
        _start_fill(box, app, _rebuild)

    scroll_content = toga.Box(style=Pack(direction=COLUMN, flex=1))
    scroll_content_ref[0] = scroll_content
    _start_fill(scroll_content, app, _rebuild)

    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
    return toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))


def _start_fill(
    container: toga.Box,
    app: toga.App,
    on_changed: object,
) -> None:
    dates = get_workout_dates()
    if not dates:
        container.add(toga.Label(t("no_history"), style=Pack(margin=16)))
        return

    # First batch — sync, so screen shows content before it's pushed onto nav stack
    for date in dates[:_BATCH_SIZE]:
        _add_date_section(container, date, app, on_changed)

    remaining = dates[_BATCH_SIZE:]
    if not remaining:
        return

    async def _load_rest(widget: object) -> None:
        import asyncio

        for i in range(0, len(remaining), _BATCH_SIZE):
            for date in remaining[i : i + _BATCH_SIZE]:
                _add_date_section(container, date, app, on_changed)
            await asyncio.sleep(0)

    app.add_background_task(_load_rest)


def _add_date_section(
    container: toga.Box, date: str, app: toga.App, on_changed: object
) -> None:
    try:
        display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        display_date = date
    async def on_delete_workout(widget: toga.Widget, date: str = date) -> None:
        result = await app.dialog(
            toga.ConfirmDialog(
                t("delete_workout"),
                t("confirm_delete_workout").format(date=date),
            )
        )
        if result:
            delete_workout_by_date(date)
            on_changed()  # type: ignore[operator]

    muscle_names = get_muscle_group_names_for_date(date)
    muscle_label = ", ".join(muscle_names) if muscle_names else ""

    header_col = toga.Box(
        children=[
            toga.Label(display_date, style=Pack(font_size=FONT_MD, margin_bottom=2)),
            *([
                toga.Label(muscle_label, style=Pack(font_size=FONT_SM, color="#757575"))
            ] if muscle_label else []),
        ],
        style=Pack(direction=COLUMN, flex=1, margin=SPACE_SM),
    )

    container.add(
        toga.Box(
            children=[
                header_col,
                toga.Button(
                    t("delete_workout"),
                    on_press=on_delete_workout,
                    style=themed_pack(margin=SPACE_SM, background_color=COLOR_BTN_DANGER()),
                ),
            ],
            style=Pack(direction=ROW),
        )
    )

    log_box = toga.Box(style=Pack(direction=COLUMN))
    populate_workout_log(log_box, date, app, on_set_changed=on_changed, reverse=False)  # type: ignore[arg-type]
    container.add(log_box)

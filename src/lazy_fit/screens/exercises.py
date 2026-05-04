"""Exercises screen — filtered by muscle group."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.i18n import t
from lazy_fit.db.models import get_exercises_by_muscle_group, MuscleGroup, Exercise
from lazy_fit.ui_constants import COLOR_BTN_PRIMARY, COLOR_BTN_SECONDARY, themed_pack


def build(app: toga.App, muscle_group: MuscleGroup) -> toga.Box:
    """Build and return the exercises screen for *muscle_group*."""

    exercises: list[Exercise] = get_exercises_by_muscle_group(muscle_group.id)

    scroll_content = toga.Box(style=Pack(direction=COLUMN, flex=1))

    if not exercises:
        scroll_content.add(
            toga.Label(t("no_exercises"), style=Pack(margin=16))
        )
    else:
        for ex in exercises:
            _add_exercise_row(app, scroll_content, ex, muscle_group)

    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))

    root = toga.Box(
        children=[scroll],
        style=Pack(direction=COLUMN, flex=1),
    )
    return root


def _add_exercise_row(
    app: toga.App, container: toga.Box, ex: Exercise, mg: MuscleGroup
) -> None:
    def on_tap(widget: toga.Widget, ex: Exercise = ex) -> None:
        from lazy_fit.screens.log_set import build as build_log
        app.nav_push(build_log(app, ex), ex.name)

    if ex.rest_days_remaining is not None and ex.rest_days_remaining > 0:
        rest = t("rest_days_remaining").format(days=ex.rest_days_remaining)
        button_text = f"{ex.name} — {rest}"
    else:
        button_text = ex.name

    resting = (
        (ex.rest_days_remaining is not None and ex.rest_days_remaining > 0)
        or mg.weekly_limit_reached
    )
    style = themed_pack(margin=8, flex=1, background_color=COLOR_BTN_SECONDARY()) if resting else themed_pack(margin=8, flex=1, background_color=COLOR_BTN_PRIMARY())
    container.add(toga.Button(button_text, on_press=on_tap, style=style))

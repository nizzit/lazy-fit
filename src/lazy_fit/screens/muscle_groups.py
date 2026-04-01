"""Muscle Groups screen — first step of workout recording."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import get_all_muscle_groups, MuscleGroup


def build(app: toga.App) -> toga.Box:
    """Build and return the muscle groups screen."""

    muscle_groups: list[MuscleGroup] = get_all_muscle_groups()

    scroll_content = toga.Box(style=Pack(direction=COLUMN, flex=1))

    if not muscle_groups:
        scroll_content.add(
            toga.Label(t("no_muscle_groups"), style=Pack(margin=16))
        )
    else:
        for mg in muscle_groups:
            _add_mg_row(app, scroll_content, mg)

    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))

    root = toga.Box(
        children=[scroll],
        style=Pack(direction=COLUMN, flex=1),
    )
    return root


def _add_mg_row(app: toga.App, container: toga.Box, mg: MuscleGroup) -> None:
    def on_tap(widget: toga.Widget, mg: MuscleGroup = mg) -> None:
        from lazy_fit.screens.exercises import build as build_ex
        app.nav_push(build_ex(app, mg), mg.name)

    label_text = mg.name
    if mg.weekly_sets:
        label_text += f"  —  " + t("weekly_sets_target").format(n=mg.weekly_sets)

    row = toga.Box(
        children=[
            toga.Label(label_text, style=Pack(flex=1, margin=4)),
            toga.Button("›", on_press=on_tap, style=Pack(margin=4, width=40)),
        ],
        style=Pack(direction=ROW, margin=8),
    )
    container.add(row)

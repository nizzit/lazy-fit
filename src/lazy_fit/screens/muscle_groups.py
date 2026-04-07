"""Muscle Groups screen — first step of workout recording."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import get_muscle_groups_with_weekly_stats, MuscleGroup


def build(app: toga.App) -> toga.Box:
    """Build and return the muscle groups screen."""

    muscle_groups: list[MuscleGroup] = get_muscle_groups_with_weekly_stats()

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

    # Button label: name + weekly progress
    if mg.weekly_sets is not None and mg.weekly_sets > 0:
        button_text = f"{mg.name} ({mg.completed_sets}/{mg.weekly_sets})"
    else:
        button_text = f"{mg.name} ({mg.completed_sets})"

    button = toga.Button(button_text, on_press=on_tap, style=Pack(flex=1))

    row_children: list[toga.Widget] = [button]

    if mg.rest_days_remaining is not None and mg.rest_days_remaining > 0:
        rest_label = toga.Label(
            t("rest_days_remaining").format(days=mg.rest_days_remaining),
            style=Pack(margin_right=8, margin_top=8, color="gray"),
        )
        row_children.append(rest_label)

    container.add(
        toga.Box(
            children=row_children,
            style=Pack(direction=ROW, margin=4),
        )
    )

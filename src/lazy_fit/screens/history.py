"""Workout History screen — list of past workouts by date."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import get_workout_dates, get_sets_for_date


def build(app: toga.App) -> toga.Box:
    """Build and return the history screen."""

    dates = get_workout_dates()

    scroll_content = toga.Box(style=Pack(direction=COLUMN, flex=1))

    if not dates:
        scroll_content.add(toga.Label(t("no_history"), style=Pack(margin=16)))
    else:
        for date in dates:
            _add_date_row(app, scroll_content, date)

    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
    root = toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))
    return root


def _add_date_row(app: toga.App, container: toga.Box, date: str) -> None:
    sets = get_sets_for_date(date)
    n_sets = len(sets)
    muscles = ", ".join(sorted({s.exercise_name.split()[0] for s in sets}))  # rough summary

    def on_tap(widget: toga.Widget, date: str = date) -> None:
        from lazy_fit.screens.workout_detail import build as build_detail
        app.nav_push(build_detail(app, date), t("workout_detail").format(date=date))

    row = toga.Box(
        children=[
            toga.Box(
                children=[
                    toga.Label(date, style=Pack(font_size=15, margin=(4, 4, 0, 4))),
                    toga.Label(
                        t("sets_count").format(n=n_sets),
                        style=Pack(margin=(0, 4, 4, 4)),
                    ),
                ],
                style=Pack(direction=COLUMN, flex=1),
            ),
            toga.Button("›", on_press=on_tap, style=Pack(margin=4, width=40)),
        ],
        style=Pack(direction=ROW, margin=8),
    )
    container.add(row)

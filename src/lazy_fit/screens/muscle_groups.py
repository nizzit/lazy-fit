"""Muscle Groups screen — first step of workout recording."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.i18n import t
from lazy_fit.db.models import get_muscle_groups_with_weekly_stats, MuscleGroup
from lazy_fit.ui_constants import COLOR_BTN_PRIMARY, COLOR_BTN_SECONDARY, themed_pack


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
        app.nav_push(build_ex(app, mg), mg.name, refresh_fn=lambda: build_ex(app, mg))

    # Button label: name + weekly progress [+ rest days if resting]
    if mg.weekly_sets is not None and mg.weekly_sets > 0:
        progress = f"{mg.completed_sets}/{mg.weekly_sets}"
    else:
        progress = str(mg.completed_sets)

    if mg.rest_days_remaining is not None and mg.rest_days_remaining > 0:
        rest = t("rest_days_remaining").format(days=mg.rest_days_remaining)
        button_text = f"{mg.name} ({progress}) — {rest}"
    else:
        button_text = f"{mg.name} ({progress})"

    resting = (mg.rest_days_remaining is not None and mg.rest_days_remaining > 0) or mg.weekly_limit_reached
    style = themed_pack(margin=8, flex=1, background_color=COLOR_BTN_SECONDARY()) if resting else themed_pack(margin=8, flex=1, background_color=COLOR_BTN_PRIMARY())
    container.add(toga.Button(button_text, on_press=on_tap, style=style))

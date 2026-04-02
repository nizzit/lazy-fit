"""Home screen — entry point of the app."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.i18n import t
from lazy_fit.db.models import get_last_exercise_today


def build(app: toga.App) -> toga.Box:
    """Build and return the home screen widget tree."""

    last_exercise = get_last_exercise_today()

    def on_start_workout(widget: toga.Widget) -> None:
        from lazy_fit.screens.muscle_groups import build as build_mg
        app.nav_push(build_mg(app), t("muscle_groups"))

    def on_continue_workout(widget: toga.Widget) -> None:
        from lazy_fit.screens.log_set import build as build_log_set
        app.nav_push(build_log_set(app, last_exercise), t("log_set"))

    def on_history(widget: toga.Widget) -> None:
        from lazy_fit.screens.history import build as build_hist
        app.nav_push(build_hist(app), t("history"))

    def on_settings(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings import build as build_settings
        app.nav_push(build_settings(app), t("settings_title"))

    btn_style = Pack(margin=12, width=240)

    buttons: list[toga.Widget] = []

    if last_exercise is not None:
        buttons.append(
            toga.Button(t("continue_workout"), on_press=on_continue_workout, style=btn_style)
        )

    buttons.append(toga.Button(t("start_workout"), on_press=on_start_workout, style=btn_style))
    buttons.append(toga.Button(t("history"), on_press=on_history, style=btn_style))
    buttons.append(toga.Button(t("settings"), on_press=on_settings, style=btn_style))

    root = toga.Box(
        children=buttons,
        style=Pack(direction=COLUMN, align_items="center", margin=32, flex=1),
    )
    return root

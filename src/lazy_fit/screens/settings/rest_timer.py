"""Rest Timer settings screen."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.widgets import StepperInput


def build(app: toga.App) -> toga.Box:
    """Build and return the rest timer settings screen."""

    from lazy_fit.db.models import get_setting, set_setting

    rest_enabled = get_setting("rest_timer_enabled", "0") == "1"
    try:
        rest_secs = int(get_setting("rest_timer_seconds", "60"))
    except ValueError:
        rest_secs = 60

    def on_rest_toggle(widget: toga.Widget) -> None:
        set_setting("rest_timer_enabled", "1" if widget.value else "0")

    def on_rest_duration_change(widget: toga.Widget) -> None:
        try:
            val = int(duration_input.value or 60)
        except (TypeError, ValueError):
            val = 60
        set_setting("rest_timer_seconds", str(val))

    rest_switch = toga.Switch(
        "",
        value=rest_enabled,
        on_change=on_rest_toggle,
        style=Pack(margin_left=8),
    )

    duration_input = StepperInput(
        min=5,
        max=600,
        step=5,
        value=rest_secs,
        on_change=on_rest_duration_change,
        style=Pack(flex=1, margin=4),
    )

    toggle_row = toga.Box(
        children=[
            toga.Label(t("rest_timer_on"), style=Pack(margin=4, flex=1)),
            rest_switch,
        ],
        style=Pack(direction=ROW, margin=4),
    )

    duration_row = toga.Box(
        children=[
            toga.Label(t("rest_timer_duration"), style=Pack(margin=4, width=160)),
            duration_input,
        ],
        style=Pack(direction=ROW, margin=4),
    )

    return toga.Box(
        children=[toggle_row, duration_row],
        style=Pack(direction=COLUMN, margin=16),
    )

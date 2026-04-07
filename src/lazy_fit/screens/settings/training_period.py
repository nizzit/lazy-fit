"""Training Period settings screen."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t


def build(app: toga.App) -> toga.Box:
    """Build and return the training period settings screen."""

    from lazy_fit.db.models import get_setting, set_setting

    current_mode = get_setting("training_period", "since_monday")

    mode_ref: list[str] = [current_mode]

    def on_since_monday(widget: toga.Widget) -> None:
        if widget.value:
            mode_ref[0] = "since_monday"
            last7_switch.value = False
            set_setting("training_period", "since_monday")

    def on_last_7_days(widget: toga.Widget) -> None:
        if widget.value:
            mode_ref[0] = "last_7_days"
            monday_switch.value = False
            set_setting("training_period", "last_7_days")

    monday_switch = toga.Switch(
        "",
        value=(current_mode == "since_monday"),
        on_change=on_since_monday,
        style=Pack(margin_left=8),
    )

    last7_switch = toga.Switch(
        "",
        value=(current_mode == "last_7_days"),
        on_change=on_last_7_days,
        style=Pack(margin_left=8),
    )

    monday_row = toga.Box(
        children=[
            toga.Label(
                t("training_period_since_monday"),
                style=Pack(margin=4, flex=1),
            ),
            monday_switch,
        ],
        style=Pack(direction=ROW, margin=4),
    )

    last7_row = toga.Box(
        children=[
            toga.Label(
                t("training_period_last_7_days"),
                style=Pack(margin=4, flex=1),
            ),
            last7_switch,
        ],
        style=Pack(direction=ROW, margin=4),
    )

    return toga.Box(
        children=[monday_row, last7_row],
        style=Pack(direction=COLUMN, margin=16),
    )

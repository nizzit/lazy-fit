"""Training Plan settings screen — weekly period mode + rest days per muscle group."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.widgets import StepperInput


def build(app: toga.App) -> toga.Box:
    """Build and return the training plan settings screen."""

    from lazy_fit.db.models import (
        get_all_muscle_groups,
        get_setting,
        set_setting,
    )

    current_mode = get_setting("training_period", "since_monday")

    # ------------------------------------------------------------------ #
    # Section: weekly period                                               #
    # ------------------------------------------------------------------ #

    def on_since_monday(widget: toga.Widget) -> None:
        if widget.value:
            last7_switch.value = False
            set_setting("training_period", "since_monday")

    def on_last_7_days(widget: toga.Widget) -> None:
        if widget.value:
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

    week_section = toga.Box(
        children=[
            toga.Label(
                t("training_period_week_section"),
                style=Pack(margin=4, font_weight="bold"),
            ),
            toga.Box(
                children=[
                    toga.Label(
                        t("training_period_since_monday"),
                        style=Pack(margin=4, flex=1),
                    ),
                    monday_switch,
                ],
                style=Pack(direction=ROW, margin=4),
            ),
            toga.Box(
                children=[
                    toga.Label(
                        t("training_period_last_7_days"),
                        style=Pack(margin=4, flex=1),
                    ),
                    last7_switch,
                ],
                style=Pack(direction=ROW, margin=4),
            ),
        ],
        style=Pack(direction=COLUMN),
    )

    # ------------------------------------------------------------------ #
    # Section: rest days per muscle group                                  #
    # ------------------------------------------------------------------ #

    muscle_groups = get_all_muscle_groups()

    rest_rows: list[toga.Widget] = [
        toga.Label(
            t("rest_days_section"),
            style=Pack(margin=4, font_weight="bold"),
        ),
    ]

    for mg in muscle_groups:

        def _make_handler(mg_id: int) -> object:
            def on_change(widget: toga.Widget) -> None:
                try:
                    val = int(widget.value or 0)
                except (TypeError, ValueError):
                    val = 0
                set_setting(f"rest_days_mg_{mg_id}", str(val))

            return on_change

        try:
            saved = int(get_setting(f"rest_days_mg_{mg.id}", "0"))
        except ValueError:
            saved = 0

        stepper = StepperInput(
            min=0,
            max=14,
            step=1,
            value=saved,
            on_change=_make_handler(mg.id),
            style=Pack(width=140, margin=4),
        )

        rest_rows.append(
            toga.Box(
                children=[
                    toga.Label(mg.name, style=Pack(margin=4, flex=1)),
                    stepper,
                ],
                style=Pack(direction=ROW, margin=4),
            )
        )

    if len(rest_rows) == 1:
        # Only the header — no muscle groups defined yet
        rest_rows.append(
            toga.Label(t("no_muscle_groups"), style=Pack(margin=4, color="gray"))
        )

    rest_section = toga.Box(
        children=rest_rows,
        style=Pack(direction=COLUMN),
    )

    # ------------------------------------------------------------------ #
    # Root                                                                 #
    # ------------------------------------------------------------------ #

    scroll_content = toga.Box(
        children=[week_section, rest_section],
        style=Pack(direction=COLUMN, margin=16),
    )

    return toga.ScrollContainer(
        content=scroll_content,
        style=Pack(flex=1),
    )

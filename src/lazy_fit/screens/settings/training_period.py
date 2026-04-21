"""Training Plan settings screen — weekly period mode + global rest days."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.widgets import StepperInput


def build(app: toga.App) -> toga.Box:
    """Build and return the training plan settings screen."""

    from lazy_fit.db.models import get_setting, set_setting

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
                    toga.Label(t("training_period_since_monday"), style=Pack(margin=4, flex=1)),
                    monday_switch,
                ],
                style=Pack(direction=ROW, margin=4),
            ),
            toga.Box(
                children=[
                    toga.Label(t("training_period_last_7_days"), style=Pack(margin=4, flex=1)),
                    last7_switch,
                ],
                style=Pack(direction=ROW, margin=4),
            ),
        ],
        style=Pack(direction=COLUMN),
    )

    # ------------------------------------------------------------------ #
    # Section: global rest days                                            #
    # ------------------------------------------------------------------ #

    try:
        saved_rest = int(get_setting("rest_days", "0"))
    except ValueError:
        saved_rest = 0
    try:
        saved_limit_exercise = int(get_setting("daily_sets_limit_exercise", "0"))
    except ValueError:
        saved_limit_exercise = 0
    try:
        saved_limit_mg = int(get_setting("daily_sets_limit_muscle_group", "0"))
    except ValueError:
        saved_limit_mg = 0

    def on_rest_days_change(widget: toga.Widget) -> None:
        try:
            val = int(widget.value or 0)
        except (TypeError, ValueError):
            val = 0
        set_setting("rest_days", str(val))

    def on_exercise_limit_change(widget: toga.Widget) -> None:
        try:
            val = int(widget.value or 0)
        except (TypeError, ValueError):
            val = 0
        set_setting("daily_sets_limit_exercise", str(val))

    def on_mg_limit_change(widget: toga.Widget) -> None:
        try:
            val = int(widget.value or 0)
        except (TypeError, ValueError):
            val = 0
        set_setting("daily_sets_limit_muscle_group", str(val))

    rest_stepper = StepperInput(
        min=0,
        max=14,
        step=1,
        value=saved_rest,
        on_change=on_rest_days_change,
        style=Pack(flex=1, margin=4),
    )

    exercise_limit_stepper = StepperInput(
        min=0,
        max=50,
        step=1,
        value=saved_limit_exercise,
        on_change=on_exercise_limit_change,
        style=Pack(flex=1, margin=4),
    )

    mg_limit_stepper = StepperInput(
        min=0,
        max=50,
        step=1,
        value=saved_limit_mg,
        on_change=on_mg_limit_change,
        style=Pack(flex=1, margin=4),
    )

    def _limit_row(label_key: str, stepper: StepperInput) -> toga.Box:
        return toga.Box(
            children=[
                toga.Box(
                    children=[toga.Label(t(label_key), style=Pack(margin_left=4))],
                    style=Pack(direction=ROW),
                ),
                toga.Box(
                    children=[toga.Box(style=Pack(flex=1)), stepper],
                    style=Pack(direction=ROW, margin_bottom=4),
                ),
            ],
            style=Pack(direction=COLUMN, margin_top=4),
        )

    rest_section = toga.Box(
        children=[
            toga.Label(
                t("rest_days_section"),
                style=Pack(margin=4, font_weight="bold"),
            ),
            toga.Box(
                children=[
                    toga.Box(
                        children=[toga.Label(t("rest_days_label"), style=Pack(margin_left=4))],
                        style=Pack(direction=ROW),
                    ),
                    toga.Box(
                        children=[toga.Box(style=Pack(flex=1)), rest_stepper],
                        style=Pack(direction=ROW, margin_bottom=4),
                    ),
                ],
                style=Pack(direction=COLUMN, margin_top=4),
            ),
            _limit_row("daily_sets_limit_exercise_label", exercise_limit_stepper),
            _limit_row("daily_sets_limit_muscle_group_label", mg_limit_stepper),
        ],
        style=Pack(direction=COLUMN),
    )

    # ------------------------------------------------------------------ #
    # Root                                                                 #
    # ------------------------------------------------------------------ #

    return toga.Box(
        children=[week_section, rest_section],
        style=Pack(direction=COLUMN, margin=16),
    )

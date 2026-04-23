"""Rest Timer settings screen."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.ui_constants import SPACE_MD, SPACE_XS
from lazy_fit.widgets import StepperInput
from lazy_fit.screens.settings._crud import build_form_field, wrap_scroll


def build(app: toga.App) -> toga.Box:
    """Build and return the rest timer settings screen."""

    from lazy_fit.db.models import get_setting, set_setting

    rest_enabled = get_setting("rest_timer_enabled", "0") == "1"
    try:
        rest_secs = int(get_setting("rest_timer_seconds", "60"))
    except ValueError:
        rest_secs = 60
    try:
        wake_lock_delay = int(get_setting("wake_lock_delay", "5"))
    except ValueError:
        wake_lock_delay = 5

    def on_rest_toggle(widget: toga.Widget) -> None:
        set_setting("rest_timer_enabled", "1" if widget.value else "0")

    def on_rest_duration_change(widget: toga.Widget) -> None:
        try:
            val = int(duration_input.value or 60)
        except (TypeError, ValueError):
            val = 60
        set_setting("rest_timer_seconds", str(val))

    def on_wake_lock_delay_change(widget: toga.Widget) -> None:
        try:
            val = int(delay_input.value or 5)
        except (TypeError, ValueError):
            val = 5
        set_setting("wake_lock_delay", str(val))

    rest_switch = toga.Switch(
        "",
        value=rest_enabled,
        on_change=on_rest_toggle,
        style=Pack(margin_left=SPACE_MD),
    )

    duration_input = StepperInput(
        min=5,
        max=600,
        step=5,
        value=rest_secs,
        on_change=on_rest_duration_change,
        style=Pack(margin=SPACE_XS),
    )

    delay_input = StepperInput(
        min=0,
        max=60,
        step=5,
        value=wake_lock_delay,
        on_change=on_wake_lock_delay_change,
        style=Pack(margin=SPACE_XS),
    )

    toggle_row = toga.Box(
        children=[
            toga.Label(t("rest_timer_on"), style=Pack(margin=SPACE_XS, flex=1)),
            rest_switch,
        ],
        style=Pack(direction=ROW, margin=SPACE_XS),
    )

    duration_row = build_form_field("rest_timer_duration", duration_input)
    delay_row = build_form_field("wake_lock_delay", delay_input)

    form_box = toga.Box(
        children=[toggle_row, duration_row, delay_row],
        style=Pack(direction=COLUMN, margin=SPACE_MD),
    )
    return wrap_scroll(form_box)

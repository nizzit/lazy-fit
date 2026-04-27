"""Universal Timer screen — stopwatch (counts up) or countdown."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.android_api import (
    acquire_wake_lock,
    release_wake_lock,
    request_notification_permission,
    send_notification,
)
from lazy_fit.i18n import t
from lazy_fit.ui_constants import BTN_TIMER_W, COLOR_BTN_PRIMARY, FONT_LG, FONT_XL

_log = logging.getLogger("lazy_fit")


def _fmt_time(secs: int) -> str:
    mm = secs // 60
    ss = secs % 60
    return f"{mm:02d}:{ss:02d}"


def build(
    app: toga.App,
    *,
    mode: str,
    on_done: Callable,
    stop_label: str,
    initial_secs: int = 0,
    header: str = "",
) -> None:
    """Build the timer screen and push it onto the nav stack.

    mode:
        "stopwatch" — counts up from 0; on_done(elapsed_secs) called on stop.
        "countdown" — counts down from initial_secs; on_done() called on stop or 0.

    Pressing the nav back button minimises the timer to a banner; pressing
    the banner's "Return" button restores the full timer screen.
    """
    if mode == "countdown":
        request_notification_permission()

    # Cancel any existing background timer before starting a new one.
    if app.active_timer is not None:
        app.active_timer["running"][0] = False
        release_wake_lock(app.active_timer["wake_lock_ref"][0])
        app.active_timer["wake_lock_ref"][0] = None
        app.active_timer = None

    running = [True]
    elapsed = [initial_secs if mode == "countdown" else 0]
    wake_lock_ref: list[object | None] = [None]
    time_label_ref: list[Optional[toga.Label]] = [None]
    done = [False]
    minimized = [False]

    screen_title = t("rest_timer") if mode == "countdown" else t("timer")

    def _do_finish() -> None:
        if done[0]:
            return
        done[0] = True
        release_wake_lock(wake_lock_ref[0])
        wake_lock_ref[0] = None
        was_minimized = (
            app.active_timer is not None
            and app.active_timer.get("screen_widget") is not None
            and len(app._nav_stack) > 0
            and app._nav_stack[-1][0] is not app.active_timer["screen_widget"]
        )
        app.active_timer = None
        if mode == "stopwatch":
            on_done(elapsed[0])
        else:
            on_done()
        if was_minimized:
            # Timer screen was already popped — just refresh to remove banner.
            app._render_current()
        else:
            app.nav_pop()

    def _stop_and_done(widget: Optional[toga.Widget] = None) -> None:
        running[0] = False
        _do_finish()

    def _minimize() -> None:
        """Called when user presses back on the timer screen."""
        if done[0]:
            return
        minimized[0] = True
        from lazy_fit.db.models import set_setting
        set_setting("rest_timer_minimized", "1")
        # nav_pop removes timer from stack; _render_current will show the banner
        # because active_timer is still set and screen_widget != current top.
        app.nav_pop()

    async def _timer_loop() -> None:
        await asyncio.sleep(1)
        while running[0]:
            if mode == "stopwatch":
                elapsed[0] += 1
                txt = _fmt_time(elapsed[0])
            else:
                elapsed[0] -= 1
                if elapsed[0] <= 0:
                    elapsed[0] = 0
                    running[0] = False
                    txt = _fmt_time(0)
                    _sync_labels(txt)
                    send_notification(
                        t("rest_timer"),
                        t("rest_timer_done"),
                        channel_id="lazy_fit_timer",
                        channel_name=t("rest_timer"),
                    )
                    await asyncio.sleep(0.5)
                    # Finish timer immediately, but keep wake lock alive for
                    # a configurable delay so the screen stays on a bit longer.
                    from lazy_fit.db.models import get_setting
                    try:
                        delay = int(get_setting("wake_lock_delay", "5"))
                    except (ValueError, TypeError):
                        delay = 5
                    deferred_ref = wake_lock_ref[0]
                    wake_lock_ref[0] = None  # prevent _do_finish from releasing
                    _do_finish()
                    if delay > 0 and deferred_ref is not None:
                        await asyncio.sleep(delay)
                    release_wake_lock(deferred_ref)
                    return
                txt = _fmt_time(elapsed[0])

            _sync_labels(txt)
            await asyncio.sleep(1)

    def _sync_labels(txt: str) -> None:
        if time_label_ref[0] is not None:
            time_label_ref[0].text = txt
        if app.active_timer is not None:
            app.active_timer["banner_text"] = txt
            bl = app.active_timer.get("banner_label")
            if bl is not None:
                bl.text = f"⏱ {txt}"

    wake_lock_ref[0] = acquire_wake_lock()

    time_label = toga.Label(
        _fmt_time(elapsed[0]),
        style=Pack(font_size=FONT_XL, margin_bottom=24, text_align="center"),
    )
    time_label_ref[0] = time_label

    stop_btn = toga.Button(
        stop_label,
        on_press=_stop_and_done,
        style=Pack(margin=8, width=BTN_TIMER_W, background_color=COLOR_BTN_PRIMARY),
    )

    center_children: list[toga.Widget] = []
    if header:
        center_children.append(
            toga.Label(
                header,
                style=Pack(font_size=FONT_LG, margin_bottom=32, text_align="center"),
            )
        )
    center_children.append(time_label)
    center_children.append(stop_btn)

    center_box = toga.Box(
        children=center_children,
        style=Pack(direction=COLUMN, align_items="center"),
    )

    root = toga.Box(
        children=[
            toga.Box(style=Pack(flex=1)),
            center_box,
            toga.Box(style=Pack(flex=1)),
        ],
        style=Pack(direction=COLUMN, flex=1),
    )

    # Register app-level timer state before pushing (banner needs it).
    app.active_timer = {
        "running": running,
        "elapsed": elapsed,
        "mode": mode,
        "wake_lock_ref": wake_lock_ref,
        "banner_label": None,       # assigned by _render_current when banner is shown
        "banner_text": _fmt_time(elapsed[0]),
        "screen_widget": root,
        "screen_title": screen_title,
        "minimize_fn": _minimize,
        "show_back": mode == "countdown",
    }

    asyncio.create_task(_timer_loop())

    # Stopwatch has no back button — user must press the stop button.
    # Countdown shows a back button that minimises the timer.
    app.nav_push(root, screen_title, back_fn=_minimize, show_back=(mode == "countdown"))

    if mode == "countdown":
        from lazy_fit.db.models import get_setting
        if get_setting("rest_timer_minimized", "0") == "1":
            _minimize()

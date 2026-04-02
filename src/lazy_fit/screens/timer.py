"""Universal Timer screen — stopwatch (counts up) or countdown."""

from __future__ import annotations

import logging
import sys
from typing import Callable

_log = logging.getLogger("lazy_fit")

import toga
from toga.style import Pack
from toga.style.pack import COLUMN


def _acquire_wake_lock() -> object | None:
    if sys.platform != "android":
        return None
    try:
        from android.os import PowerManager  # type: ignore[import-untyped]
        from org.beeware.android import MainActivity  # type: ignore[import-untyped]

        activity = MainActivity.singletonThis
        power_manager = activity.getSystemService("power")
        wake_lock = power_manager.newWakeLock(
            PowerManager.SCREEN_DIM_WAKE_LOCK,
            "LazyFit:TimerWakeLock",
        )
        wake_lock.acquire()
        return wake_lock
    except Exception as e:
        _log.exception("Failed to acquire wake lock: %s: %s", type(e).__name__, e)
        return None


def _release_wake_lock(wake_lock: object | None) -> None:
    if wake_lock is None:
        return
    try:
        if wake_lock.isHeld():  # type: ignore[union-attr]
            wake_lock.release()  # type: ignore[union-attr]
    except Exception:
        pass


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
) -> toga.Box:
    """Build and return the timer screen.

    mode:
        "stopwatch" — counts up from 0; on_done(elapsed_secs) called on stop.
        "countdown" — counts down from initial_secs; on_done() called on stop or 0.
    """

    running = [True]
    elapsed = [initial_secs if mode == "countdown" else 0]
    wake_lock_ref: list[object | None] = [None]
    time_label_ref: list[toga.Label | None] = [None]
    popped = [False]

    def _do_finish() -> None:
        if popped[0]:
            return
        popped[0] = True
        if mode == "stopwatch":
            on_done(elapsed[0])
        else:
            on_done()
        app.nav_pop()

    def _stop_and_done(widget: toga.Widget | None = None) -> None:
        running[0] = False
        _release_wake_lock(wake_lock_ref[0])
        wake_lock_ref[0] = None
        _do_finish()

    def _tick() -> None:
        if not running[0]:
            return

        if mode == "stopwatch":
            elapsed[0] += 1
            if time_label_ref[0]:
                time_label_ref[0].text = _fmt_time(elapsed[0])

            async def _wait(app: toga.App, **kwargs: object) -> None:
                import asyncio

                await asyncio.sleep(1)
                _tick()

            app.add_background_task(_wait)

        else:
            elapsed[0] -= 1
            if elapsed[0] <= 0:
                elapsed[0] = 0
                running[0] = False
                _release_wake_lock(wake_lock_ref[0])
                wake_lock_ref[0] = None
                if time_label_ref[0]:
                    time_label_ref[0].text = _fmt_time(0)

                async def _auto_finish(app: toga.App, **kwargs: object) -> None:
                    import asyncio

                    await asyncio.sleep(0.5)
                    _do_finish()

                app.add_background_task(_auto_finish)
                return

            if time_label_ref[0]:
                time_label_ref[0].text = _fmt_time(elapsed[0])

            async def _wait_cd(app: toga.App, **kwargs: object) -> None:
                import asyncio

                await asyncio.sleep(1)
                _tick()

            app.add_background_task(_wait_cd)

    wake_lock_ref[0] = _acquire_wake_lock()

    async def _start(app: toga.App, **kwargs: object) -> None:
        import asyncio

        await asyncio.sleep(1)
        _tick()

    app.add_background_task(_start)

    time_label = toga.Label(
        _fmt_time(elapsed[0]),
        style=Pack(font_size=64, margin_bottom=24, text_align="center"),
    )
    time_label_ref[0] = time_label

    stop_btn = toga.Button(
        stop_label,
        on_press=_stop_and_done,
        style=Pack(margin=8, width=160),
    )

    center_children: list[toga.Widget] = []
    if header:
        center_children.append(
            toga.Label(
                header,
                style=Pack(font_size=18, margin_bottom=32, text_align="center"),
            )
        )
    center_children.append(time_label)
    center_children.append(stop_btn)

    center_box = toga.Box(
        children=center_children,
        style=Pack(direction=COLUMN, align_items="center"),
    )

    return toga.Box(
        children=[
            toga.Box(style=Pack(flex=1)),
            center_box,
            toga.Box(style=Pack(flex=1)),
        ],
        style=Pack(direction=COLUMN, flex=1),
    )

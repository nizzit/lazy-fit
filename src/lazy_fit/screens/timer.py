"""Universal Timer screen — stopwatch (counts up) or countdown."""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Callable

_log = logging.getLogger("lazy_fit")

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.i18n import t


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


def _request_notification_permission() -> None:
    if sys.platform != "android":
        return
    try:
        from android.content.pm import PackageManager  # type: ignore[import-untyped]
        from android.os import Build  # type: ignore[import-untyped]
        from org.beeware.android import MainActivity  # type: ignore[import-untyped]

        if Build.VERSION.SDK_INT < 33:
            return

        activity = MainActivity.singletonThis
        perm = "android.permission.POST_NOTIFICATIONS"
        if activity.checkSelfPermission(perm) != PackageManager.PERMISSION_GRANTED:
            activity.requestPermissions([perm], 42)
    except Exception as e:
        _log.exception(
            "Failed to request notification permission: %s: %s", type(e).__name__, e
        )


def _send_notification(title: str, body: str) -> None:
    if sys.platform != "android":
        return
    try:
        from android.app import Notification, NotificationChannel, NotificationManager, PendingIntent  # type: ignore[import-untyped]
        from android.content import Context, Intent  # type: ignore[import-untyped]
        from java import jclass  # type: ignore[import-untyped]
        from org.beeware.android import MainActivity  # type: ignore[import-untyped]

        activity = MainActivity.singletonThis
        nm = activity.getSystemService(Context.NOTIFICATION_SERVICE)

        channel_id = "lazy_fit_timer"
        channel = NotificationChannel(
            channel_id,
            t("rest_timer"),
            NotificationManager.IMPORTANCE_HIGH,
        )
        nm.createNotificationChannel(channel)

        intent = Intent(activity, activity.getClass())
        intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        tap_intent = PendingIntent.getActivity(
            activity,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE,
        )

        NotificationBuilder = jclass("android.app.Notification$Builder")
        builder = NotificationBuilder(activity, channel_id)
        builder.setContentTitle(title)
        builder.setContentText(body)
        builder.setSmallIcon(activity.getApplicationInfo().icon)
        builder.setContentIntent(tap_intent)
        builder.setAutoCancel(True)

        nm.notify(1, builder.build())
    except Exception as e:
        _log.exception("Failed to send notification: %s: %s", type(e).__name__, e)


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

    if mode == "countdown":
        _request_notification_permission()

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

    async def _timer_loop() -> None:
        await asyncio.sleep(1)
        while running[0]:
            if mode == "stopwatch":
                elapsed[0] += 1
                if time_label_ref[0]:
                    time_label_ref[0].text = _fmt_time(elapsed[0])
            else:
                elapsed[0] -= 1
                if elapsed[0] <= 0:
                    elapsed[0] = 0
                    running[0] = False
                    _release_wake_lock(wake_lock_ref[0])
                    wake_lock_ref[0] = None
                    if time_label_ref[0]:
                        time_label_ref[0].text = _fmt_time(0)
                    _send_notification(t("rest_timer"), t("rest_timer_done"))
                    await asyncio.sleep(0.5)
                    _do_finish()
                    return
                if time_label_ref[0]:
                    time_label_ref[0].text = _fmt_time(elapsed[0])
            await asyncio.sleep(1)

    wake_lock_ref[0] = _acquire_wake_lock()
    asyncio.create_task(_timer_loop())

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

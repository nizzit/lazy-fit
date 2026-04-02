"""Android platform API helpers — wake lock, notifications."""

from __future__ import annotations

import logging
import sys

_log = logging.getLogger("lazy_fit")

_NOTIFICATION_REQUEST_CODE = 42
_NOTIFICATION_ID = 1


def acquire_wake_lock() -> object | None:
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


def release_wake_lock(wake_lock: object | None) -> None:
    if wake_lock is None:
        return
    try:
        if wake_lock.isHeld():  # type: ignore[union-attr]
            wake_lock.release()  # type: ignore[union-attr]
    except Exception:
        pass


def request_notification_permission() -> None:
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
            activity.requestPermissions([perm], _NOTIFICATION_REQUEST_CODE)
    except Exception as e:
        _log.exception(
            "Failed to request notification permission: %s: %s", type(e).__name__, e
        )


def send_notification(
    title: str,
    body: str,
    *,
    channel_id: str,
    channel_name: str,
) -> None:
    if sys.platform != "android":
        return
    try:
        from android.app import NotificationChannel, NotificationManager, PendingIntent  # type: ignore[import-untyped]
        from android.content import Context, Intent  # type: ignore[import-untyped]
        from java import jclass  # type: ignore[import-untyped]
        from org.beeware.android import MainActivity  # type: ignore[import-untyped]

        activity = MainActivity.singletonThis
        nm = activity.getSystemService(Context.NOTIFICATION_SERVICE)

        channel = NotificationChannel(
            channel_id,
            channel_name,
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

        nm.notify(_NOTIFICATION_ID, builder.build())
    except Exception as e:
        _log.exception("Failed to send notification: %s: %s", type(e).__name__, e)

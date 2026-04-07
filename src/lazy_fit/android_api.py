"""Android platform API helpers — wake lock, notifications, file share/pick."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable, Optional

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


def share_file(app: object, path: Path) -> None:
    """Share *path* via Android share sheet (ACTION_SEND).

    Uses the FileProvider registered by Briefcase under the authority
    ``com.lazyfit.lazy-fit.fileprovider``.  The file must reside inside
    a path exposed by ``file_paths.xml`` (cache dir works out of the box).
    """
    if sys.platform != "android":
        return
    try:
        from android.content import Intent  # type: ignore[import-untyped]
        from androidx.core.content import FileProvider  # type: ignore[import-untyped]
        from java import jclass  # type: ignore[import-untyped]
        from org.beeware.android import MainActivity  # type: ignore[import-untyped]

        activity = MainActivity.singletonThis
        JavaFile = jclass("java.io.File")
        java_file = JavaFile(str(path))
        authority = "com.lazyfit.lazy-fit.fileprovider"
        uri = FileProvider.getUriForFile(activity, authority, java_file)

        intent = Intent(Intent.ACTION_SEND)
        intent.setType("application/json")
        intent.putExtra(Intent.EXTRA_STREAM, uri)
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        chooser = Intent.createChooser(intent, "")
        app._impl.start_activity(chooser, on_complete=lambda *_: None)  # type: ignore[union-attr]
    except Exception as e:
        _log.exception("share_file failed: %s: %s", type(e).__name__, e)


def pick_file(app: object, on_complete: Callable[[int, object], None]) -> None:
    """Open Android file picker (ACTION_GET_CONTENT) for a JSON file.

    *on_complete* is called with ``(result_code, result_data)`` when the
    user selects a file or cancels.  ``result_code == -1`` (RESULT_OK) means
    a file was selected; ``result_data.getData()`` returns the content URI.
    """
    if sys.platform != "android":
        return
    try:
        from android.content import Intent  # type: ignore[import-untyped]

        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("application/json")
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        app._impl.start_activity(intent, on_complete=on_complete)  # type: ignore[union-attr]
    except Exception as e:
        _log.exception("pick_file failed: %s: %s", type(e).__name__, e)


def read_uri(uri: object) -> Optional[str]:
    """Read the text content of an Android content URI.

    Returns the decoded string, or ``None`` on error.
    """
    if sys.platform != "android":
        return None
    try:
        from org.beeware.android import MainActivity  # type: ignore[import-untyped]

        activity = MainActivity.singletonThis
        stream = activity.getContentResolver().openInputStream(uri)
        # Read all bytes from the Java InputStream into a Python bytearray
        buf = bytearray()
        chunk = bytearray(4096)
        while True:
            n = stream.read(chunk)
            if n == -1:
                break
            buf.extend(chunk[:n])
        stream.close()
        return buf.decode("utf-8")
    except Exception as e:
        _log.exception("read_uri failed: %s: %s", type(e).__name__, e)
        return None


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

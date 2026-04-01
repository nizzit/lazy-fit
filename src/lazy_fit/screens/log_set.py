"""Log Set screen — record a set + show today's workout summary."""

from __future__ import annotations

import datetime
import sys
from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.widgets import StepperInput
from lazy_fit.screens._workout_log import populate_workout_log
from lazy_fit.db.models import (
    Exercise,
    get_all_equipment,
    get_sets_for_date,
    create_workout_set,
    get_last_value_for_exercise,
    get_last_equipment_for_exercise,
)


def _today() -> str:
    return datetime.date.today().isoformat()


# ------------------------------------------------------------------ wake lock helpers
def _acquire_wake_lock() -> object | None:
    """Acquire an Android SCREEN_DIM_WAKE_LOCK to prevent screen sleep.

    Returns the WakeLock instance on Android, or None on other platforms.
    """
    if sys.platform != "android":
        return None
    try:
        from jnius import autoclass  # type: ignore[import-untyped]

        Context = autoclass("android.content.Context")
        PythonActivity = autoclass("org.beeware.android.MainActivity")
        activity = PythonActivity.sActivity
        power_manager = activity.getSystemService(Context.POWER_SERVICE)
        PowerManager = autoclass("android.os.PowerManager")
        wake_lock = power_manager.newWakeLock(
            PowerManager.SCREEN_DIM_WAKE_LOCK,
            "LazyFit:TimerWakeLock",
        )
        wake_lock.acquire()
        return wake_lock
    except Exception:
        return None


def _release_wake_lock(wake_lock: object | None) -> None:
    """Release a previously acquired Android wake lock."""
    if wake_lock is None:
        return
    try:
        if wake_lock.isHeld():  # type: ignore[union-attr]
            wake_lock.release()  # type: ignore[union-attr]
    except Exception:
        pass


def build(app: toga.App, exercise: Exercise) -> toga.Box:
    """Build and return the log-set screen for *exercise*."""

    today = _today()
    equipment_list = get_all_equipment()
    last_value = get_last_value_for_exercise(exercise.id)
    last_equipment_id = get_last_equipment_for_exercise(exercise.id)

    # ------------------------------------------------------------------ state
    timer_running = [False]
    timer_elapsed = [0]  # seconds
    timer_handle = [None]
    wake_lock_ref: list[object | None] = [None]

    rest_running = [False]
    rest_remaining = [0]

    # ------------------------------------------------------------------ refs
    # We keep mutable references so inner functions can update them
    timer_label_ref: list[Optional[toga.Label]] = [None]
    value_input_ref: list[Optional[toga.NumberInput]] = [None]
    equip_select_ref: list[Optional[toga.Selection]] = [None]
    history_box_ref: list[Optional[toga.Box]] = [None]
    rest_box_ref: list[Optional[toga.Box]] = [None]
    rest_label_ref: list[Optional[toga.Label]] = [None]
    rest_skip_btn_ref: list[Optional[toga.Button]] = [None]

    # ------------------------------------------------------------------ timer helpers
    def _fmt_elapsed(secs: int) -> str:
        mm = secs // 60
        ss = secs % 60
        return f"{mm:02d}:{ss:02d}"

    def _tick(widget: toga.Widget | None = None) -> None:
        if timer_running[0]:
            timer_elapsed[0] += 1
            if timer_label_ref[0]:
                timer_label_ref[0].text = _fmt_elapsed(timer_elapsed[0])
            timer_handle[0] = app.add_background_task(_tick_after)

    def _tick_after(widget: toga.Widget | None = None) -> None:
        """Schedule next tick after 1 second using a background task."""
        import asyncio

        async def _wait_and_tick(app: toga.App, **kwargs: object) -> None:
            await asyncio.sleep(1)
            _tick()

        app.add_background_task(_wait_and_tick)

    def on_timer_start(widget: toga.Widget) -> None:
        if not timer_running[0]:
            timer_running[0] = True
            wake_lock_ref[0] = _acquire_wake_lock()
            _tick_after()

    def on_timer_stop(widget: toga.Widget) -> None:
        timer_running[0] = False
        _release_wake_lock(wake_lock_ref[0])
        wake_lock_ref[0] = None
        # Auto-fill the duration input
        if value_input_ref[0] is not None:
            value_input_ref[0].value = timer_elapsed[0]

    def on_timer_reset(widget: toga.Widget) -> None:
        timer_running[0] = False
        _release_wake_lock(wake_lock_ref[0])
        wake_lock_ref[0] = None
        timer_elapsed[0] = 0
        if timer_label_ref[0]:
            timer_label_ref[0].text = "00:00"
        if value_input_ref[0] is not None:
            value_input_ref[0].value = 0

    # ------------------------------------------------------------------ rest timer
    def _fmt_remaining(secs: int) -> str:
        mm = secs // 60
        ss = secs % 60
        return f"{mm:02d}:{ss:02d}"

    def _clear_rest_box() -> None:
        rest_running[0] = False
        box = rest_box_ref[0]
        if box is not None:
            for child in list(box.children):
                box.remove(child)

    def _on_skip_rest(widget: toga.Widget) -> None:
        _clear_rest_box()

    def _rest_tick() -> None:
        if not rest_running[0]:
            return
        rest_remaining[0] -= 1
        if rest_remaining[0] <= 0:
            rest_running[0] = False
            lbl = rest_label_ref[0]
            if lbl is not None:
                lbl.text = t("rest_timer_done")
            btn = rest_skip_btn_ref[0]
            if btn is not None:
                box = rest_box_ref[0]
                if box is not None:
                    box.remove(btn)
                rest_skip_btn_ref[0] = None
            async def _auto_clear(app: toga.App, **kwargs: object) -> None:
                import asyncio
                await asyncio.sleep(2)
                _clear_rest_box()
            app.add_background_task(_auto_clear)
            return
        lbl = rest_label_ref[0]
        if lbl is not None:
            lbl.text = t("rest_timer_countdown").format(time=_fmt_remaining(rest_remaining[0]))
        async def _wait_tick(app: toga.App, **kwargs: object) -> None:
            import asyncio
            await asyncio.sleep(1)
            _rest_tick()
        app.add_background_task(_wait_tick)

    def _start_rest_timer() -> None:
        from lazy_fit.db.models import get_setting
        if get_setting("rest_timer_enabled", "0") != "1":
            return
        try:
            secs = int(get_setting("rest_timer_seconds", "60"))
        except ValueError:
            secs = 60
        if secs <= 0:
            return

        rest_running[0] = True
        rest_remaining[0] = secs

        box = rest_box_ref[0]
        if box is None:
            return
        for child in list(box.children):
            box.remove(child)

        rest_label = toga.Label(
            t("rest_timer_countdown").format(time=_fmt_remaining(secs)),
            style=Pack(font_size=20, margin=4),
        )
        rest_label_ref[0] = rest_label
        skip_btn = toga.Button(t("rest_timer_skip"), on_press=_on_skip_rest, style=Pack(margin=4))
        rest_skip_btn_ref[0] = skip_btn
        box.add(rest_label)
        box.add(skip_btn)

        async def _first_tick(app: toga.App, **kwargs: object) -> None:
            import asyncio
            await asyncio.sleep(1)
            _rest_tick()
        app.add_background_task(_first_tick)

    # ------------------------------------------------------------------ save
    def on_save(widget: toga.Widget) -> None:
        raw_value = value_input_ref[0].value if value_input_ref[0] else None
        try:
            int_value = int(raw_value) if raw_value is not None else 0
        except (ValueError, TypeError):
            int_value = 0

        # Equipment
        eq_id: Optional[int] = None
        if equip_select_ref[0] and equip_select_ref[0].value:
            sel = equip_select_ref[0].value
            if sel != t("no_equipment"):
                # Find equipment id by name
                for eq in equipment_list:
                    if eq.name == sel:
                        eq_id = eq.id
                        break

        if exercise.type == "reps":
            create_workout_set(today, exercise.id, reps=int_value, equipment_id=eq_id)
        else:
            create_workout_set(today, exercise.id, duration_sec=int_value, equipment_id=eq_id)

        # Keep last saved value as default for next set
        on_timer_reset(widget)
        if value_input_ref[0]:
            value_input_ref[0].value = int_value

        # Refresh history panel
        _refresh_history()

        # Start rest timer if enabled
        _start_rest_timer()

    # ------------------------------------------------------------------ history
    def _refresh_history() -> None:
        box = history_box_ref[0]
        if box is None:
            return
        # Clear existing children
        for child in list(box.children):
            box.remove(child)
        populate_workout_log(box, today, app, _refresh_history, reverse=True)

    # ------------------------------------------------------------------ build UI
    # Rest timer banner (populated dynamically after each save)
    rest_box = toga.Box(style=Pack(direction=ROW, align_items="center", margin=4))
    rest_box_ref[0] = rest_box

    # Header
    header = toga.Label(
        f"{exercise.name}  ·  {exercise.muscle_group_name}",
        style=Pack(margin=8, font_size=16),
    )

    # Input area
    value_input = StepperInput(
        min=0,
        step=1,
        value=last_value if last_value is not None else 0,
        style=Pack(flex=1, margin=4),
    )
    value_input_ref[0] = value_input

    if exercise.type == "reps":
        input_label = toga.Label(t("reps"), style=Pack(margin=4, width=120))
        input_row = toga.Box(
            children=[input_label, value_input],
            style=Pack(direction=ROW, margin=4),
        )
        form_children = [input_row]
    else:
        # Time exercise — show timer + manual input
        timer_label = toga.Label("00:00", style=Pack(font_size=32, margin=8))
        timer_label_ref[0] = timer_label

        start_btn = toga.Button(t("timer_start"), on_press=on_timer_start, style=Pack(margin=4))
        stop_btn = toga.Button(t("timer_stop"), on_press=on_timer_stop, style=Pack(margin=4))
        reset_btn = toga.Button(t("timer_reset"), on_press=on_timer_reset, style=Pack(margin=4))

        timer_controls = toga.Box(
            children=[start_btn, stop_btn, reset_btn],
            style=Pack(direction=ROW, margin=4),
        )

        input_label = toga.Label(t("duration"), style=Pack(margin=4, width=120))
        input_row = toga.Box(
            children=[input_label, value_input],
            style=Pack(direction=ROW, margin=4),
        )
        form_children = [timer_label, timer_controls, input_row]

    # Equipment picker
    equip_options = [t("no_equipment")] + [eq.name for eq in equipment_list]
    _last_equip_name = next(
        (eq.name for eq in equipment_list if eq.id == last_equipment_id), None
    )
    equip_select = toga.Selection(
        items=equip_options,
        value=_last_equip_name if _last_equip_name is not None else t("no_equipment"),
        style=Pack(flex=1, margin=4),
    )
    equip_select_ref[0] = equip_select

    equip_row = toga.Box(
        children=[
            toga.Label(t("equipment"), style=Pack(margin=4, width=120)),
            equip_select,
        ],
        style=Pack(direction=ROW, margin=4),
    )

    save_btn = toga.Button(t("save_set"), on_press=on_save, style=Pack(margin=12))

    form_box = toga.Box(
        children=form_children + [equip_row, save_btn],
        style=Pack(direction=COLUMN, margin=8),
    )

    # Today's history panel
    history_title = toga.Label(
        t("todays_workout"),
        style=Pack(margin=(12, 8, 4, 8), font_size=14),
    )
    history_box = toga.Box(style=Pack(direction=COLUMN))
    history_box_ref[0] = history_box
    populate_workout_log(history_box, today, app, _refresh_history, reverse=True)

    scroll_content = toga.Box(
        children=[rest_box, header, form_box, history_title, history_box],
        style=Pack(direction=COLUMN),
    )
    scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
    root = toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))
    return root




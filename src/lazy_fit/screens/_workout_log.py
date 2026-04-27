"""Workout log widget — shared set list for current and past workouts."""

from __future__ import annotations

from typing import Callable, Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.ui_constants import BTN_SET_W, COLOR_DIFF_DOWN, COLOR_DIFF_UP, FONT_SM, FONT_XS, SPACE_XS
from lazy_fit.db.models import WorkoutSet, get_sets_for_date, get_prev_workout_values_for_exercise


def populate_workout_log(
    box: toga.Box,
    date: str,
    app: toga.App,
    on_set_changed: Callable[[], None] | None = None,
    reverse: bool = True,
) -> None:
    """Fill *box* with sets grouped by exercise.

    If *reverse* is True (default), the most recent exercise appears first.
    If *reverse* is False, exercises appear in chronological order (first on top).
    """
    sets = get_sets_for_date(date)

    if not sets:
        box.add(toga.Label(t("no_sets_today"), style=Pack(margin=8)))
        return

    # Group by exercise_id (not name) to avoid merging same-named exercises.
    # Insertion order is preserved so groups reflect chronological exercise order.
    seen: dict[int, list[WorkoutSet]] = {}
    for ws in sets:
        if ws.exercise_id not in seen:
            seen[ws.exercise_id] = []
        seen[ws.exercise_id].append(ws)

    # Build ordered list of (name, exercise_id, sets) pairs.
    groups: list[tuple[str, int, list[WorkoutSet]]] = [
        (ex_sets[0].exercise_name, ex_id, ex_sets) for ex_id, ex_sets in seen.items()
    ]

    if reverse:
        groups.reverse()

    per_row = _buttons_per_row(app)

    for ex_name, ex_id, ex_sets in groups:
        prev_values = get_prev_workout_values_for_exercise(ex_id, date)
        box.add(toga.Label(ex_name, style=Pack(margin=(8, 8, 2, 8), font_size=FONT_SM)))
        wrap = toga.Box(style=Pack(direction=COLUMN))
        current_row = toga.Box(style=Pack(direction=ROW))
        for i, ws in enumerate(ex_sets):
            if i > 0 and i % per_row == 0:
                wrap.add(current_row)
                current_row = toga.Box(style=Pack(direction=ROW))
            _add_set_button(current_row, ws, i, prev_values, app, on_set_changed)
        if current_row.children:
            wrap.add(current_row)
        box.add(wrap)


def _set_diff(
    current_val: int, set_index: int, prev_values: list[int]
) -> tuple[Optional[str], Optional[str]]:
    """Return (diff_text, color) for a set button label.

    Returns (None, None) when there is no previous set at *set_index*
    (current workout has more sets than the previous one).
    """
    if set_index >= len(prev_values):
        return None, None
    diff = current_val - prev_values[set_index]
    if diff > 0:
        return f"+{diff}", COLOR_DIFF_UP
    if diff < 0:
        return str(diff), COLOR_DIFF_DOWN
    return "=", None


def _add_set_button(
    container: toga.Box,
    ws: WorkoutSet,
    set_index: int,
    prev_values: list[int],
    app: toga.App,
    on_set_changed: Callable[[], None] | None = None,
) -> None:
    from lazy_fit.ui_constants import FONT_XS

    if ws.exercise_type == "reps":
        current_val = ws.reps or 0
        base_label = str(current_val)
    else:
        current_val = ws.duration_sec or 0
        secs = current_val
        base_label = f"{secs // 60:02d}:{secs % 60:02d}"

    diff_text, diff_color = _set_diff(current_val, set_index, prev_values)

    def on_press(widget: toga.Widget, ws: WorkoutSet = ws) -> None:
        from lazy_fit.screens.edit_set import build as build_edit
        from lazy_fit.db.models import get_all_equipment as _get_equip

        def _on_saved() -> None:
            if on_set_changed:
                on_set_changed()

        screen = build_edit(app, ws, _get_equip(), _on_saved)
        app.nav_push(screen, t("edit_set"))

    btn = toga.Button(base_label, on_press=on_press, style=Pack(width=BTN_SET_W))

    children: list[toga.Widget] = [btn]
    if diff_text is not None:
        diff_style = Pack(
            width=BTN_SET_W,
            font_size=FONT_XS,
            text_align="center",
            **({"color": diff_color} if diff_color else {}),
        )
        children.append(toga.Label(diff_text, style=diff_style))

    container.add(
        toga.Box(children=children, style=Pack(direction=COLUMN, margin=SPACE_XS))
    )


def _buttons_per_row(app: toga.App, slot_width: int = 72) -> int:
    try:
        screen_w = app.main_window.screen.size.width
        return max(2, int(screen_w // slot_width))
    except Exception:
        return 4

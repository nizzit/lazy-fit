"""Workout log widget — shared set list for current and past workouts."""

from __future__ import annotations

from typing import Callable

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import WorkoutSet, get_sets_for_date


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

    # Build ordered list of (name, sets) pairs; exercise_name is stable per id.
    groups: list[tuple[str, list[WorkoutSet]]] = [
        (ex_sets[0].exercise_name, ex_sets) for ex_sets in seen.values()
    ]

    if reverse:
        groups.reverse()

    per_row = _buttons_per_row(app)

    for ex_name, ex_sets in groups:
        box.add(toga.Label(ex_name, style=Pack(margin=(8, 8, 2, 8), font_size=13)))
        wrap = toga.Box(style=Pack(direction=COLUMN))
        current_row = toga.Box(style=Pack(direction=ROW))
        for i, ws in enumerate(ex_sets):
            if i > 0 and i % per_row == 0:
                wrap.add(current_row)
                current_row = toga.Box(style=Pack(direction=ROW))
            _add_set_button(current_row, ws, app, on_set_changed)
        if current_row.children:
            wrap.add(current_row)
        box.add(wrap)


def _add_set_button(
    container: toga.Box,
    ws: WorkoutSet,
    app: toga.App,
    on_set_changed: Callable[[], None] | None = None,
) -> None:
    if ws.exercise_type == "reps":
        label = str(ws.reps or 0)
    else:
        secs = ws.duration_sec or 0
        label = f"{secs // 60:02d}:{secs % 60:02d}"

    def on_press(widget: toga.Widget, ws: WorkoutSet = ws) -> None:
        from lazy_fit.screens.edit_set import build as build_edit
        from lazy_fit.db.models import get_all_equipment as _get_equip

        def _on_saved() -> None:
            if on_set_changed:
                on_set_changed()

        screen = build_edit(app, ws, _get_equip(), _on_saved)
        app.nav_push(screen, t("edit_set"))

    container.add(toga.Button(label, on_press=on_press, style=Pack(margin=4, width=64)))


def _buttons_per_row(app: toga.App, slot_width: int = 72) -> int:
    try:
        screen_w = app.main_window.screen.size.width
        return max(2, int(screen_w // slot_width))
    except Exception:
        return 4

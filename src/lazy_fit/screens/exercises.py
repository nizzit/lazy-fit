"""Exercises screen — filtered by muscle group."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.i18n import t
from lazy_fit.db.models import (
    get_exercises_by_muscle_group,
    get_muscle_groups_with_weekly_stats,
    MuscleGroup,
    Exercise,
)
from lazy_fit.ui_constants import (
    COLOR_BTN_ADD,
    COLOR_BTN_PRIMARY,
    COLOR_BTN_SECONDARY,
    SPACE_SM,
    themed_pack,
)


def build(app: toga.App, muscle_group: MuscleGroup) -> toga.Box:
    """Build and return the exercises screen for *muscle_group*."""

    def _refresh() -> None:
        scroll.content = _build_content()

    def on_add(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings.manage_exercises import _show_form

        _show_form(
            app,
            None,
            _refresh,
            preselect_mg_ids=[muscle_group.id],
            refresh_on_cancel=True,
        )

    def _build_content() -> toga.Box:
        exercises: list[Exercise] = get_exercises_by_muscle_group(muscle_group.id)

        mg_stats = get_muscle_groups_with_weekly_stats()
        mg_status = {}
        for mg in mg_stats:
            if mg.rest_days_remaining is not None and mg.rest_days_remaining > 0:
                mg_status[mg.id] = 2  # resting
            elif mg.weekly_sets is None or mg.weekly_sets == 0:
                mg_status[mg.id] = 0  # not completed (no plan)
            elif mg.completed_sets < mg.weekly_sets:
                mg_status[mg.id] = 0  # not completed
            else:
                mg_status[mg.id] = 1  # completed

        def _group_status(ex: Exercise) -> int:
            statuses = [mg_status.get(mid, 0) for mid in ex.muscle_group_ids]
            if not statuses:
                return 0
            if 2 in statuses:
                return 2
            if 0 in statuses:
                return 0
            return 1

        def _exercise_status(ex: Exercise) -> int:
            # 0 never, 1 active, 2 completed, 3 resting
            if getattr(ex, "completed_sets", 0) == 0:
                return 0
            if (ex.rest_days_remaining is not None and ex.rest_days_remaining > 0):
                return 3
            if getattr(ex, "weekly_sets", None) is not None and getattr(ex, "completed_sets", 0) >= getattr(ex, "weekly_sets", 0):
                return 2
            return 1

        def _secondary(ex: Exercise) -> tuple:
            s = _exercise_status(ex)
            completed = getattr(ex, "completed_sets", 0)
            weekly = getattr(ex, "weekly_sets", None)

            if s == 0:  # never → higher weekly target first
                return (-(weekly or 0),)
            if s == 1:  # active → fewer completed first
                return (completed,)
            if s == 2:  # completed → more overcompletion lower
                over = (completed - (weekly or 0)) if weekly else 0
                return (over,)
            if s == 3:  # resting → fewer rest days first
                return (ex.rest_days_remaining or 0,)
            return (0,)

        exercises = sorted(
            exercises,
            key=lambda ex: (_group_status(ex), _secondary(ex), ex.name.lower()),
        )

        scroll_content = toga.Box(style=Pack(direction=COLUMN, flex=1))

        if not exercises:
            scroll_content.add(
                toga.Label(t("no_exercises"), style=Pack(margin=16))
            )
            scroll_content.add(
                toga.Button(
                    f"+ {t('add')}",
                    on_press=on_add,
                    style=themed_pack(
                        margin=SPACE_SM,
                        background_color=COLOR_BTN_ADD(),
                    ),
                )
            )
        else:
            for ex in exercises:
                _add_exercise_row(app, scroll_content, ex, muscle_group)

        return scroll_content

    scroll = toga.ScrollContainer(content=_build_content(), style=Pack(flex=1))

    root = toga.Box(
        children=[scroll],
        style=Pack(direction=COLUMN, flex=1),
    )
    return root


def _add_exercise_row(
    app: toga.App, container: toga.Box, ex: Exercise, mg: MuscleGroup
) -> None:
    def on_tap(widget: toga.Widget, ex: Exercise = ex) -> None:
        from lazy_fit.screens.log_set import build as build_log
        app.nav_push(build_log(app, ex), ex.name)

    if ex.rest_days_remaining is not None and ex.rest_days_remaining > 0:
        rest = t("rest_days_remaining").format(days=ex.rest_days_remaining)
        button_text = f"{ex.name} — {rest}"
    else:
        button_text = ex.name

    resting = (
        (ex.rest_days_remaining is not None and ex.rest_days_remaining > 0)
        or mg.weekly_limit_reached
    )
    style = themed_pack(margin=8, flex=1, background_color=COLOR_BTN_SECONDARY()) if resting else themed_pack(margin=8, flex=1, background_color=COLOR_BTN_PRIMARY())
    container.add(toga.Button(button_text, on_press=on_tap, style=style))

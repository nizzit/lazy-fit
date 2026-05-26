"""CRUD helpers for all entities."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date as _date
from typing import Optional

from .connection import get_connection


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class MuscleGroup:
    id: int
    name: str
    weekly_sets: Optional[int]
    rest_days: Optional[int] = None  # per-group override; None = use global
    completed_sets: int = 0
    rest_days_remaining: Optional[int] = None  # computed: days left in rest
    trained_today: bool = False
    weekly_limit_reached: bool = False  # computed: completed_sets >= weekly_sets
    is_builtin: int = 0  # 1 for built-in groups (e.g. cardio); cannot be deleted
    builtin_key: Optional[str] = None  # i18n key for built-in group display name

    @property
    def display_name(self) -> str:
        """Return the localised display name (built-ins translate via i18n key)."""
        if self.builtin_key:
            from lazy_fit.i18n import t
            return t(self.builtin_key)
        return self.name


@dataclass
class Equipment:
    id: int
    name: str


@dataclass
class Exercise:
    id: int
    name: str
    type: str  # 'reps' | 'time' | 'cardio'
    muscle_group_ids: list[int] = field(default_factory=list)
    muscle_group_names: list[str] = field(default_factory=list)
    rest_days_remaining: Optional[int] = None  # computed: max rest days remaining across linked muscle groups


@dataclass
class WorkoutSet:
    id: int
    date: str
    exercise_id: int
    order_index: int
    reps: Optional[int]
    duration_sec: Optional[int]
    equipment_id: Optional[int]
    created_at: str
    exercise_name: str = ""
    equipment_name: str = ""
    exercise_type: str = ""
    avg_hr: Optional[int] = None  # average heart rate (cardio only)
    max_hr: Optional[int] = None  # maximum heart rate (cardio only)


# ---------------------------------------------------------------------------
# MuscleGroup
# ---------------------------------------------------------------------------


def get_muscle_group_by_id(mg_id: int) -> Optional[MuscleGroup]:
    row = (
        get_connection()
        .execute("SELECT id, name, weekly_sets, rest_days, is_builtin, builtin_key FROM muscle_group WHERE id = ?", (mg_id,))
        .fetchone()
    )
    return MuscleGroup(**dict(row)) if row else None


def get_all_muscle_groups() -> list[MuscleGroup]:
    rows = (
        get_connection()
        .execute("SELECT id, name, weekly_sets, rest_days, is_builtin, builtin_key FROM muscle_group ORDER BY name")
        .fetchall()
    )
    return [MuscleGroup(**dict(r)) for r in rows]


def create_muscle_group(
    name: str,
    weekly_sets: Optional[int] = None,
    rest_days: Optional[int] = None,
) -> MuscleGroup:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO muscle_group(name, weekly_sets, rest_days) VALUES (?, ?, ?)",
        (name, weekly_sets, rest_days),
    )
    conn.commit()
    return MuscleGroup(id=cur.lastrowid, name=name, weekly_sets=weekly_sets, rest_days=rest_days)


def update_muscle_group(
    mg_id: int,
    name: str,
    weekly_sets: Optional[int],
    rest_days: Optional[int] = None,
) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE muscle_group SET name=?, weekly_sets=?, rest_days=? WHERE id=?",
        (name, weekly_sets, rest_days, mg_id),
    )
    conn.commit()


def delete_muscle_group(mg_id: int) -> None:
    conn = get_connection()
    # Guard: built-in groups cannot be deleted
    row = conn.execute("SELECT is_builtin FROM muscle_group WHERE id=?", (mg_id,)).fetchone()
    if row and row["is_builtin"]:
        return
    conn.execute("DELETE FROM muscle_group WHERE id=?", (mg_id,))
    conn.commit()


def get_cardio_group() -> Optional[MuscleGroup]:
    """Return the built-in cardio muscle group, or None if not found."""
    row = (
        get_connection()
        .execute(
            "SELECT id, name, weekly_sets, rest_days, is_builtin, builtin_key FROM muscle_group WHERE is_builtin = 1 LIMIT 1"
        )
        .fetchone()
    )
    return MuscleGroup(**dict(row)) if row else None


# ---------------------------------------------------------------------------
# Equipment
# ---------------------------------------------------------------------------


def get_all_equipment() -> list[Equipment]:
    rows = (
        get_connection()
        .execute("SELECT id, name FROM equipment ORDER BY name")
        .fetchall()
    )
    return [Equipment(**dict(r)) for r in rows]


def create_equipment(name: str) -> Equipment:
    conn = get_connection()
    cur = conn.execute("INSERT INTO equipment(name) VALUES (?)", (name,))
    conn.commit()
    return Equipment(id=cur.lastrowid, name=name)


def update_equipment(eq_id: int, name: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE equipment SET name=? WHERE id=?", (name, eq_id))
    conn.commit()


def delete_equipment(eq_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM equipment WHERE id=?", (eq_id,))
    conn.commit()


# ---------------------------------------------------------------------------
# Exercise — internal helpers
# ---------------------------------------------------------------------------


def _rows_to_exercises(rows: list) -> list[Exercise]:
    """Convert flat JOIN rows (one row per exercise_muscle_group link) to Exercise list."""
    from lazy_fit.i18n import t as _t
    exercises: dict[int, Exercise] = {}
    for r in rows:
        d = dict(r)
        ex_id = d["id"]
        if ex_id not in exercises:
            exercises[ex_id] = Exercise(
                id=ex_id,
                name=d["name"],
                type=d["type"],
                muscle_group_ids=[],
                muscle_group_names=[],
            )
        mg_id = d.get("muscle_group_id")
        bk = d.get("muscle_group_builtin_key")
        mg_name = _t(bk) if bk else d.get("muscle_group_name")
        if mg_id is not None and mg_id not in exercises[ex_id].muscle_group_ids:
            exercises[ex_id].muscle_group_ids.append(mg_id)
        if mg_name is not None and mg_name not in exercises[ex_id].muscle_group_names:
            exercises[ex_id].muscle_group_names.append(mg_name)
    return list(exercises.values())


def _fetch_exercise_by_id(ex_id: int) -> Optional[Exercise]:
    rows = (
        get_connection()
        .execute(
            """
            SELECT e.id, e.name, e.type,
                   emg.muscle_group_id, mg.name AS muscle_group_name,
                   mg.builtin_key AS muscle_group_builtin_key
            FROM exercise e
            LEFT JOIN exercise_muscle_group emg ON emg.exercise_id = e.id
            LEFT JOIN muscle_group mg ON mg.id = emg.muscle_group_id
            WHERE e.id = ?
            ORDER BY mg.name
            """,
            (ex_id,),
        )
        .fetchall()
    )
    if not rows:
        return None
    return _rows_to_exercises(rows)[0]


def _set_exercise_muscle_groups(conn, ex_id: int, muscle_group_ids: list[int]) -> None:
    conn.execute("DELETE FROM exercise_muscle_group WHERE exercise_id = ?", (ex_id,))
    for mg_id in muscle_group_ids:
        conn.execute(
            "INSERT OR IGNORE INTO exercise_muscle_group(exercise_id, muscle_group_id) VALUES (?, ?)",
            (ex_id, mg_id),
        )


# ---------------------------------------------------------------------------
# Exercise — public CRUD
# ---------------------------------------------------------------------------


def get_all_exercises() -> list[Exercise]:
    rows = (
        get_connection()
        .execute("""
            SELECT e.id, e.name, e.type,
                   emg.muscle_group_id, mg.name AS muscle_group_name,
                   mg.builtin_key AS muscle_group_builtin_key
            FROM exercise e
            LEFT JOIN exercise_muscle_group emg ON emg.exercise_id = e.id
            LEFT JOIN muscle_group mg ON mg.id = emg.muscle_group_id
            ORDER BY e.name, mg.name
        """)
        .fetchall()
    )
    return _rows_to_exercises(rows)


def get_exercises_by_muscle_group(mg_id: int) -> list[Exercise]:
    rows = (
        get_connection()
        .execute(
            """
            SELECT e.id, e.name, e.type,
                   emg2.muscle_group_id, mg2.name AS muscle_group_name,
                   mg2.builtin_key AS muscle_group_builtin_key
            FROM exercise e
            JOIN exercise_muscle_group emg ON emg.exercise_id = e.id AND emg.muscle_group_id = ?
            LEFT JOIN exercise_muscle_group emg2 ON emg2.exercise_id = e.id
            LEFT JOIN muscle_group mg2 ON mg2.id = emg2.muscle_group_id
            ORDER BY e.name, mg2.name
            """,
            (mg_id,),
        )
        .fetchall()
    )
    exercises = _rows_to_exercises(rows)

    # Build rest map from muscle group stats: mg_id -> rest_days_remaining
    mg_stats = get_muscle_groups_with_weekly_stats()
    mg_rest: dict[int, int] = {
        mg.id: mg.rest_days_remaining
        for mg in mg_stats
        if mg.rest_days_remaining is not None and mg.rest_days_remaining > 0
    }

    if mg_rest:
        for ex in exercises:
            remaining_values = [
                mg_rest[mid] for mid in ex.muscle_group_ids if mid in mg_rest
            ]
            if remaining_values:
                ex.rest_days_remaining = max(remaining_values)

    # --- compute weekly progress per exercise (respect training period setting) ---
    conn = get_connection()

    week_start, week_end = get_week_range()

    counts = {
        r["exercise_id"]: r["cnt"]
        for r in conn.execute(
            """
            SELECT exercise_id, COUNT(*) as cnt
            FROM workout_set
            WHERE date BETWEEN ? AND ?
            GROUP BY exercise_id
            """,
            (week_start, week_end),
        ).fetchall()
    }

    # map mg_id -> weekly_sets
    mg_stats = get_muscle_groups_with_weekly_stats()
    mg_weekly = {mg.id: mg.weekly_sets for mg in mg_stats if mg.weekly_sets}

    for ex in exercises:
        ex.completed_sets = counts.get(ex.id, 0)  # type: ignore[attr-defined]
        # take max weekly target among linked groups
        targets = [mg_weekly[mid] for mid in ex.muscle_group_ids if mid in mg_weekly]
        ex.weekly_sets = max(targets) if targets else None  # type: ignore[attr-defined]

    return exercises



def create_exercise(name: str, muscle_group_ids: list[int], ex_type: str) -> Exercise:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO exercise(name, type) VALUES (?, ?)",
        (name, ex_type),
    )
    ex_id = cur.lastrowid
    _set_exercise_muscle_groups(conn, ex_id, muscle_group_ids)
    conn.commit()
    result = _fetch_exercise_by_id(ex_id)
    if result is None:
        raise RuntimeError(f"Exercise {ex_id} not found after insert")
    return result


def update_exercise(
    ex_id: int, name: str, muscle_group_ids: list[int], ex_type: str
) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE exercise SET name=?, type=? WHERE id=?",
        (name, ex_type, ex_id),
    )
    _set_exercise_muscle_groups(conn, ex_id, muscle_group_ids)
    conn.commit()


def delete_exercise(ex_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM exercise WHERE id=?", (ex_id,))
    conn.commit()


# ---------------------------------------------------------------------------
# WorkoutSet
# ---------------------------------------------------------------------------


def _row_to_workout_set(r: dict) -> WorkoutSet:
    return WorkoutSet(
        id=r["id"],
        date=r["date"],
        exercise_id=r["exercise_id"],
        order_index=r["order_index"],
        reps=r["reps"],
        duration_sec=r["duration_sec"],
        equipment_id=r["equipment_id"],
        created_at=r["created_at"],
        exercise_name=r.get("exercise_name", ""),
        equipment_name=r.get("equipment_name", "") or "",
        exercise_type=r.get("exercise_type", ""),
        avg_hr=r.get("avg_hr"),
        max_hr=r.get("max_hr"),
    )


def get_sets_for_date(date: str) -> list[WorkoutSet]:
    rows = (
        get_connection()
        .execute(
            """
        SELECT ws.*, e.name AS exercise_name, e.type AS exercise_type,
               eq.name AS equipment_name
        FROM workout_set ws
        JOIN exercise e ON e.id = ws.exercise_id
        LEFT JOIN equipment eq ON eq.id = ws.equipment_id
        WHERE ws.date = ?
        ORDER BY ws.order_index, ws.created_at
    """,
            (date,),
        )
        .fetchall()
    )
    return [_row_to_workout_set(dict(r)) for r in rows]


def get_workout_dates() -> list[str]:
    """Return distinct workout dates in descending order."""
    rows = (
        get_connection()
        .execute("SELECT DISTINCT date FROM workout_set ORDER BY date DESC")
        .fetchall()
    )
    return [r["date"] for r in rows]


def get_muscle_group_names_for_date(date: str) -> list[str]:
    """Return distinct muscle group display names trained on *date*, sorted alphabetically."""
    from lazy_fit.i18n import t as _t
    rows = (
        get_connection()
        .execute(
            """
            SELECT DISTINCT mg.name, mg.builtin_key
            FROM workout_set ws
            JOIN exercise e ON e.id = ws.exercise_id
            JOIN exercise_muscle_group emg ON emg.exercise_id = e.id
            JOIN muscle_group mg ON mg.id = emg.muscle_group_id
            WHERE ws.date = ?
            ORDER BY mg.name
            """,
            (date,),
        )
        .fetchall()
    )
    result = []
    for r in rows:
        bk = r["builtin_key"]
        result.append(_t(bk) if bk else r["name"])
    return result


def create_workout_set(
    date: str,
    exercise_id: int,
    reps: Optional[int] = None,
    duration_sec: Optional[int] = None,
    equipment_id: Optional[int] = None,
    avg_hr: Optional[int] = None,
    max_hr: Optional[int] = None,
) -> WorkoutSet:
    conn = get_connection()
    # Determine next order_index for this date
    row = conn.execute(
        "SELECT COALESCE(MAX(order_index), -1) + 1 AS next_idx FROM workout_set WHERE date=?",
        (date,),
    ).fetchone()
    order_index = row["next_idx"]
    cur = conn.execute(
        """INSERT INTO workout_set(date, exercise_id, order_index, reps, duration_sec, equipment_id, avg_hr, max_hr)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (date, exercise_id, order_index, reps, duration_sec, equipment_id, avg_hr, max_hr),
    )
    conn.commit()
    row = conn.execute(
        """
        SELECT ws.*, e.name AS exercise_name, e.type AS exercise_type,
               eq.name AS equipment_name
        FROM workout_set ws
        JOIN exercise e ON e.id = ws.exercise_id
        LEFT JOIN equipment eq ON eq.id = ws.equipment_id
        WHERE ws.id = ?
    """,
        (cur.lastrowid,),
    ).fetchone()
    return _row_to_workout_set(dict(row))


def update_workout_set(
    set_id: int,
    reps: Optional[int] = None,
    duration_sec: Optional[int] = None,
    equipment_id: Optional[int] = None,
    avg_hr: Optional[int] = None,
    max_hr: Optional[int] = None,
) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE workout_set SET reps=?, duration_sec=?, equipment_id=?, avg_hr=?, max_hr=? WHERE id=?",
        (reps, duration_sec, equipment_id, avg_hr, max_hr, set_id),
    )
    conn.commit()


def delete_workout_set(set_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM workout_set WHERE id=?", (set_id,))
    conn.commit()


def delete_workout_by_date(date: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM workout_set WHERE date=?", (date,))
    conn.commit()


def get_prev_workout_values_for_exercise(
    exercise_id: int,
    before_date: str,
    equipment_id: Optional[int] = None,
    _filter_equipment: bool = False,
) -> list[int]:
    """Return set values from the most recent workout before *before_date*.

    Values are reps (for 'reps' exercises) or duration_sec (for 'time' exercises),
    in set order. Empty list if no prior workout exists for *exercise_id*.

    When *_filter_equipment* is True the query is restricted to sets whose
    equipment_id matches *equipment_id* (None means no equipment / IS NULL).
    """
    conn = get_connection()
    if _filter_equipment:
        if equipment_id is None:
            date_row = conn.execute(
                """
                SELECT DISTINCT date FROM workout_set
                WHERE exercise_id = ? AND date < ? AND equipment_id IS NULL
                ORDER BY date DESC LIMIT 1
                """,
                (exercise_id, before_date),
            ).fetchone()
        else:
            date_row = conn.execute(
                """
                SELECT DISTINCT date FROM workout_set
                WHERE exercise_id = ? AND date < ? AND equipment_id = ?
                ORDER BY date DESC LIMIT 1
                """,
                (exercise_id, before_date, equipment_id),
            ).fetchone()
    else:
        date_row = conn.execute(
            """
            SELECT DISTINCT date FROM workout_set
            WHERE exercise_id = ? AND date < ?
            ORDER BY date DESC LIMIT 1
            """,
            (exercise_id, before_date),
        ).fetchone()
    if date_row is None:
        return []
    prev_date = date_row["date"]
    if _filter_equipment:
        if equipment_id is None:
            rows = conn.execute(
                """
                SELECT reps, duration_sec FROM workout_set
                WHERE exercise_id = ? AND date = ? AND equipment_id IS NULL
                ORDER BY order_index, created_at
                """,
                (exercise_id, prev_date),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT reps, duration_sec FROM workout_set
                WHERE exercise_id = ? AND date = ? AND equipment_id = ?
                ORDER BY order_index, created_at
                """,
                (exercise_id, prev_date, equipment_id),
            ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT reps, duration_sec FROM workout_set
            WHERE exercise_id = ? AND date = ?
            ORDER BY order_index, created_at
            """,
            (exercise_id, prev_date),
        ).fetchall()
    result: list[int] = []
    for r in rows:
        v = r["reps"] if r["reps"] is not None else r["duration_sec"]
        result.append(v if v is not None else 0)
    return result


def get_last_equipment_for_exercise(exercise_id: int) -> Optional[int]:
    """Return the most recent equipment_id used for *exercise_id*, or None."""
    row = (
        get_connection()
        .execute(
            """SELECT equipment_id FROM workout_set
           WHERE exercise_id = ?
           ORDER BY date DESC, order_index DESC, created_at DESC
           LIMIT 1""",
            (exercise_id,),
        )
        .fetchone()
    )
    if row is None:
        return None
    return row["equipment_id"]


def get_last_heart_rates_for_exercise(
    exercise_id: int,
) -> tuple[Optional[int], Optional[int]]:
    """Return (avg_hr, max_hr) from the most recent cardio workout_set for *exercise_id*.

    Returns (None, None) if no previous workout exists or if both values are NULL.
    """
    row = get_connection().execute(
        """
        SELECT avg_hr, max_hr FROM workout_set
        WHERE exercise_id = ? AND (avg_hr IS NOT NULL OR max_hr IS NOT NULL)
        ORDER BY date DESC, order_index DESC, created_at DESC
        LIMIT 1
        """,
        (exercise_id,),
    ).fetchone()
    if row is None:
        return (None, None)
    return (row["avg_hr"], row["max_hr"])


# ---------------------------------------------------------------------------
# App settings
# ---------------------------------------------------------------------------


def get_setting(key: str, default: str = "") -> str:
    row = (
        get_connection()
        .execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        .fetchone()
    )
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO app_settings(key, value) VALUES(?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


# ---------------------------------------------------------------------------


def get_week_range() -> tuple[str, str]:
    """Return (start_date, end_date) ISO strings for the current training week.

    Mode is read from app_settings key ``training_period``:
    - ``"since_monday"`` (default) — Mon of current calendar week through Sun.
    - ``"last_7_days"`` — today minus 6 days through today.
    """
    from datetime import date, timedelta

    today = date.today()
    mode = get_setting("training_period", "since_monday")
    if mode == "last_7_days":
        start = today - timedelta(days=6)
        end = today
    else:
        start = today - timedelta(days=today.weekday())  # Monday
        end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


def get_weekly_sets_count_for_muscle_group(mg_id: int) -> int:
    """Return the number of sets logged in the current training week for *mg_id*."""
    week_start, week_end = get_week_range()
    row = (
        get_connection()
        .execute(
            """
        SELECT COUNT(*) AS cnt
        FROM workout_set ws
        JOIN exercise e ON e.id = ws.exercise_id
        JOIN exercise_muscle_group emg ON emg.exercise_id = e.id
        WHERE emg.muscle_group_id = ?
          AND ws.date >= ?
          AND ws.date <= ?
        """,
            (mg_id, week_start, week_end),
        )
        .fetchone()
    )
    return row["cnt"] if row else 0


def get_muscle_groups_with_weekly_stats() -> list[MuscleGroup]:
    """Return muscle groups sorted by plan progress, with resting groups at the bottom."""
    from datetime import date

    week_start, week_end = get_week_range()
    today = date.today()
    today_str = today.isoformat()

    rows = (
        get_connection()
        .execute(
            """
            SELECT
                mg.id, mg.name, mg.weekly_sets, mg.rest_days, mg.is_builtin, mg.builtin_key,
                (
                    SELECT COUNT(ws.id)
                    FROM workout_set ws
                    JOIN exercise e ON e.id = ws.exercise_id
                    JOIN exercise_muscle_group emg ON emg.exercise_id = e.id
                    WHERE emg.muscle_group_id = mg.id
                      AND ws.date >= ? AND ws.date <= ?
                ) AS completed_sets,
                (
                    SELECT COUNT(ws.id)
                    FROM workout_set ws
                    JOIN exercise e ON e.id = ws.exercise_id
                    JOIN exercise_muscle_group emg ON emg.exercise_id = e.id
                    WHERE emg.muscle_group_id = mg.id
                      AND ws.date = ?
                ) AS today_sets,
                (
                    SELECT MAX(ws.date)
                    FROM workout_set ws
                    JOIN exercise e ON e.id = ws.exercise_id
                    JOIN exercise_muscle_group emg ON emg.exercise_id = e.id
                    WHERE emg.muscle_group_id = mg.id
                ) AS last_trained
            FROM muscle_group mg
            ORDER BY mg.name
            """,
            (week_start, week_end, today_str),
        )
        .fetchall()
    )

    try:
        rest_days_setting = int(get_setting("rest_days", "0"))
    except ValueError:
        rest_days_setting = 0
    try:
        daily_limit = int(get_setting("daily_sets_limit_muscle_group", "0"))
    except ValueError:
        daily_limit = 0

    muscle_groups = []
    for r in rows:
        last_trained = date.fromisoformat(r["last_trained"]) if r["last_trained"] else None
        today_sets: int = r["today_sets"]
        limit_reached = daily_limit > 0 and today_sets >= daily_limit
        trained_today = last_trained == today if last_trained else False

        # Per-group rest_days overrides the global setting when set.
        mg_rest_days: Optional[int] = r["rest_days"]
        effective_rest = mg_rest_days if (mg_rest_days is not None) else rest_days_setting

        rest_remaining: Optional[int] = None
        if limit_reached:
            # Daily limit hit — rest starts now
            rest_remaining = effective_rest if effective_rest > 0 else 1
        elif last_trained and not trained_today and effective_rest > 0:
            # Trained on a previous day — normal rest countdown
            elapsed = (today - last_trained).days
            remaining = effective_rest - elapsed + 1
            if remaining > 0:
                rest_remaining = remaining
        # trained today but limit not reached → not resting yet

        weekly_limit = r["weekly_sets"]
        weekly_limit_reached = (
            weekly_limit is not None
            and weekly_limit > 0
            and r["completed_sets"] >= weekly_limit
        )
        mg = MuscleGroup(
            id=r["id"],
            name=r["name"],
            weekly_sets=r["weekly_sets"],
            rest_days=mg_rest_days,
            completed_sets=r["completed_sets"],
            rest_days_remaining=rest_remaining,
            trained_today=trained_today and not limit_reached,
            weekly_limit_reached=weekly_limit_reached,
            is_builtin=r["is_builtin"],
            builtin_key=r["builtin_key"],
        )
        muscle_groups.append(mg)

    def sort_key(mg: MuscleGroup) -> tuple:
        resting = mg.rest_days_remaining is not None and mg.rest_days_remaining > 0
        if resting:
            # Resting groups: sink to bottom, sorted by most days remaining first
            return (3, mg.rest_days_remaining, mg.name)
        if mg.weekly_sets is None or mg.weekly_sets == 0:
            # No plan — after active groups but before resting
            return (2, 0, mg.name)
        if mg.trained_today:
            # Trained today and limit not yet reached — highest priority
            ratio = mg.completed_sets / mg.weekly_sets
            return (0, ratio, mg.name)
        ratio = mg.completed_sets / mg.weekly_sets
        return (1, ratio, mg.name)

    muscle_groups.sort(key=sort_key)
    return muscle_groups


def get_last_exercise_today() -> Optional[Exercise]:
    """Return the Exercise from the most recent workout_set logged today, or None."""
    from datetime import date

    today = date.today().isoformat()
    row = (
        get_connection()
        .execute(
            """
        SELECT e.id
        FROM workout_set ws
        JOIN exercise e ON e.id = ws.exercise_id
        WHERE ws.date = ?
        ORDER BY ws.order_index DESC, ws.created_at DESC
        LIMIT 1
        """,
            (today,),
        )
        .fetchone()
    )
    if row is None:
        return None
    return _fetch_exercise_by_id(row["id"])


def get_default_value_for_next_set(
    exercise_id: int,
    today: str,
    equipment_id: Optional[int] = None,
    filter_by_equipment: bool = False,
) -> Optional[int]:
    """Return suggested value for the next set of *exercise_id* today.

    Uses the most recent previous workout as the reference. Returns the value at
    the same position as the next set to be logged today. When the previous
    workout has fewer sets than needed, falls back to the last value logged today
    (or the last set of the previous workout if nothing is logged yet).
    Returns None if no previous workout exists for this exercise.

    When *filter_by_equipment* is True the search is restricted to sets with
    the given *equipment_id* (None = no equipment / IS NULL).
    """
    conn = get_connection()
    # How many sets already logged today with matching equipment (= index of next set)
    if filter_by_equipment:
        if equipment_id is None:
            cnt_row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM workout_set WHERE exercise_id = ? AND date = ? AND equipment_id IS NULL",
                (exercise_id, today),
            ).fetchone()
        else:
            cnt_row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM workout_set WHERE exercise_id = ? AND date = ? AND equipment_id = ?",
                (exercise_id, today, equipment_id),
            ).fetchone()
    else:
        cnt_row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM workout_set WHERE exercise_id = ? AND date = ?",
            (exercise_id, today),
        ).fetchone()
    set_index: int = cnt_row["cnt"] if cnt_row else 0

    prev_values = get_prev_workout_values_for_exercise(
        exercise_id, today, equipment_id=equipment_id, _filter_equipment=filter_by_equipment
    )
    if not prev_values:
        return None

    if set_index < len(prev_values):
        return prev_values[set_index]

    # Previous workout has fewer sets — fall back to last value logged today
    if filter_by_equipment:
        if equipment_id is None:
            last_today = conn.execute(
                """
                SELECT reps, duration_sec FROM workout_set
                WHERE exercise_id = ? AND date = ? AND equipment_id IS NULL
                ORDER BY order_index DESC, created_at DESC
                LIMIT 1
                """,
                (exercise_id, today),
            ).fetchone()
        else:
            last_today = conn.execute(
                """
                SELECT reps, duration_sec FROM workout_set
                WHERE exercise_id = ? AND date = ? AND equipment_id = ?
                ORDER BY order_index DESC, created_at DESC
                LIMIT 1
                """,
                (exercise_id, today, equipment_id),
            ).fetchone()
    else:
        last_today = conn.execute(
            """
            SELECT reps, duration_sec FROM workout_set
            WHERE exercise_id = ? AND date = ?
            ORDER BY order_index DESC, created_at DESC
            LIMIT 1
            """,
            (exercise_id, today),
        ).fetchone()
    if last_today is not None:
        return last_today["reps"] if last_today["reps"] is not None else last_today["duration_sec"]

    # Nothing today yet — use last set of previous workout
    return prev_values[-1]


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------

# Canonical built-in group definitions: (fixed_id, builtin_key, canonical_name)
# Negative IDs are used so they never collide with AUTOINCREMENT-assigned IDs
# and remain stable across export/import cycles.
_BUILTIN_GROUPS: list[tuple[int, str, str]] = [
    (-1, "cardio_group_name", "cardio"),
]


def _migrate_builtin_id(conn: object, current_id: int, builtin_id: int, builtin_key: str) -> None:
    """Reassign a built-in group's rowid to its canonical negative value.

    Temporarily disables FK enforcement so the rowid can be changed and the
    exercise_muscle_group references updated atomically.
    """
    import sqlite3 as _sqlite3

    assert isinstance(conn, _sqlite3.Connection)
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript(f"""
            UPDATE exercise_muscle_group
               SET muscle_group_id = {builtin_id}
             WHERE muscle_group_id = {current_id};
            UPDATE muscle_group
               SET id = {builtin_id}, is_builtin = 1, builtin_key = '{builtin_key}'
             WHERE id = {current_id};
        """)
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception:
        conn.execute("PRAGMA foreign_keys = ON")
        raise


def ensure_builtin_groups() -> None:
    """Ensure all built-in muscle groups exist with correct flags and canonical IDs.

    Called after import or reset.  Handles four cases per built-in entry:
    1. Row has correct builtin_key AND correct id  → just update is_builtin flag.
    2. Row has correct builtin_key but wrong id    → migrate rowid to canonical value.
    3. No builtin_key match; row matches canonical name (old backup) → migrate + set flags.
    4. Neither exists                              → insert with explicit canonical id.
    """
    conn = get_connection()
    for builtin_id, builtin_key, canonical_name in _BUILTIN_GROUPS:
        row = conn.execute(
            "SELECT id FROM muscle_group WHERE builtin_key = ?",
            (builtin_key,),
        ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT id FROM muscle_group WHERE name = ?",
                (canonical_name,),
            ).fetchone()
        if row:
            current_id = row["id"]
            if current_id != builtin_id:
                _migrate_builtin_id(conn, current_id, builtin_id, builtin_key)
            else:
                conn.execute(
                    "UPDATE muscle_group SET is_builtin = 1, builtin_key = ? WHERE id = ?",
                    (builtin_key, builtin_id),
                )
        else:
            conn.execute(
                "INSERT INTO muscle_group(id, name, is_builtin, builtin_key) VALUES (?, ?, 1, ?)",
                (builtin_id, canonical_name, builtin_key),
            )
    conn.commit()


def export_all_data() -> dict:
    """Serialize all user data to a plain dict suitable for JSON serialisation."""
    conn = get_connection()
    muscle_groups = [
        dict(r)
        for r in conn.execute(
            "SELECT id, name, weekly_sets, is_builtin, builtin_key FROM muscle_group ORDER BY id"
        ).fetchall()
    ]
    equipment = [
        dict(r)
        for r in conn.execute("SELECT id, name FROM equipment ORDER BY id").fetchall()
    ]
    exercises = [
        dict(r)
        for r in conn.execute(
            "SELECT id, name, type FROM exercise ORDER BY id"
        ).fetchall()
    ]
    # Attach muscle_group_ids list to each exercise
    emg_rows = conn.execute(
        "SELECT exercise_id, muscle_group_id FROM exercise_muscle_group ORDER BY exercise_id, muscle_group_id"
    ).fetchall()
    emg_map: dict[int, list[int]] = {}
    for r in emg_rows:
        emg_map.setdefault(r["exercise_id"], []).append(r["muscle_group_id"])
    for ex in exercises:
        ex["muscle_group_ids"] = emg_map.get(ex["id"], [])

    workout_sets = [
        dict(r)
        for r in conn.execute(
            """SELECT id, date, exercise_id, order_index, reps,
                      duration_sec, equipment_id, avg_hr, max_hr, created_at
               FROM workout_set ORDER BY date, order_index, created_at"""
        ).fetchall()
    ]
    return {
        "version": 2,
        "exported_at": _date.today().isoformat(),
        "muscle_groups": muscle_groups,
        "equipment": equipment,
        "exercises": exercises,
        "workout_sets": workout_sets,
    }


def reset_all_data() -> None:
    """Delete all user-generated data (sets, exercises, muscle groups, equipment)."""
    from lazy_fit.db.connection import init_db

    conn = get_connection()
    conn.execute("DELETE FROM workout_set")
    conn.execute("DELETE FROM exercise_muscle_group")
    conn.execute("DELETE FROM exercise")
    conn.execute("DELETE FROM equipment")
    conn.execute("DELETE FROM muscle_group")
    conn.commit()
    init_db()  # recreate built-in groups


def import_all_data(data: dict) -> None:
    """Replace all user data with the contents of *data* (from export_all_data)."""
    conn = get_connection()
    # Delete in FK-safe order
    conn.execute("DELETE FROM workout_set")
    conn.execute("DELETE FROM exercise_muscle_group")
    conn.execute("DELETE FROM exercise")
    conn.execute("DELETE FROM equipment")
    conn.execute("DELETE FROM muscle_group")

    # Insert in FK-safe order (parents first)
    for mg in data.get("muscle_groups", []):
        conn.execute(
            "INSERT INTO muscle_group(id, name, weekly_sets, is_builtin, builtin_key) VALUES (?, ?, ?, ?, ?)",
            (mg["id"], mg["name"], mg.get("weekly_sets"), mg.get("is_builtin", 0), mg.get("builtin_key")),
        )
    for eq in data.get("equipment", []):
        conn.execute(
            "INSERT INTO equipment(id, name) VALUES (?, ?)",
            (eq["id"], eq["name"]),
        )
    for ex in data.get("exercises", []):
        conn.execute(
            "INSERT INTO exercise(id, name, type) VALUES (?, ?, ?)",
            (ex["id"], ex["name"], ex["type"]),
        )
        # Support both old format (muscle_group_id) and new (muscle_group_ids)
        mg_ids: list[int] = ex.get("muscle_group_ids") or []
        if not mg_ids and ex.get("muscle_group_id"):
            mg_ids = [ex["muscle_group_id"]]
        for mg_id in mg_ids:
            conn.execute(
                "INSERT OR IGNORE INTO exercise_muscle_group(exercise_id, muscle_group_id) VALUES (?, ?)",
                (ex["id"], mg_id),
            )
    for ws in data.get("workout_sets", []):
        conn.execute(
            """INSERT INTO workout_set
               (id, date, exercise_id, order_index, reps, duration_sec, equipment_id, avg_hr, max_hr, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ws["id"],
                ws["date"],
                ws["exercise_id"],
                ws["order_index"],
                ws.get("reps"),
                ws.get("duration_sec"),
                ws.get("equipment_id"),
                ws.get("avg_hr"),
                ws.get("max_hr"),
                ws.get("created_at", ""),
            ),
        )
    conn.commit()
    ensure_builtin_groups()  # restore / repair built-in group flags

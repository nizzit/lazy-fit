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
    completed_sets: int = 0
    rest_days_remaining: Optional[int] = None  # None = no rest rule set


@dataclass
class Equipment:
    id: int
    name: str


@dataclass
class Exercise:
    id: int
    name: str
    type: str  # 'reps' | 'time'
    muscle_group_ids: list[int] = field(default_factory=list)
    muscle_group_names: list[str] = field(default_factory=list)


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


# ---------------------------------------------------------------------------
# MuscleGroup
# ---------------------------------------------------------------------------


def get_all_muscle_groups() -> list[MuscleGroup]:
    rows = (
        get_connection()
        .execute("SELECT id, name, weekly_sets FROM muscle_group ORDER BY name")
        .fetchall()
    )
    return [MuscleGroup(**dict(r)) for r in rows]


def create_muscle_group(name: str, weekly_sets: Optional[int] = None) -> MuscleGroup:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO muscle_group(name, weekly_sets) VALUES (?, ?)",
        (name, weekly_sets),
    )
    conn.commit()
    return MuscleGroup(id=cur.lastrowid, name=name, weekly_sets=weekly_sets)


def update_muscle_group(mg_id: int, name: str, weekly_sets: Optional[int]) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE muscle_group SET name=?, weekly_sets=? WHERE id=?",
        (name, weekly_sets, mg_id),
    )
    conn.commit()


def delete_muscle_group(mg_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM muscle_group WHERE id=?", (mg_id,))
    conn.commit()


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
        mg_name = d.get("muscle_group_name")
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
                   emg.muscle_group_id, mg.name AS muscle_group_name
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
                   emg.muscle_group_id, mg.name AS muscle_group_name
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
                   emg2.muscle_group_id, mg2.name AS muscle_group_name
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
    return _rows_to_exercises(rows)


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


def create_workout_set(
    date: str,
    exercise_id: int,
    reps: Optional[int] = None,
    duration_sec: Optional[int] = None,
    equipment_id: Optional[int] = None,
) -> WorkoutSet:
    conn = get_connection()
    # Determine next order_index for this date
    row = conn.execute(
        "SELECT COALESCE(MAX(order_index), -1) + 1 AS next_idx FROM workout_set WHERE date=?",
        (date,),
    ).fetchone()
    order_index = row["next_idx"]
    cur = conn.execute(
        """INSERT INTO workout_set(date, exercise_id, order_index, reps, duration_sec, equipment_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (date, exercise_id, order_index, reps, duration_sec, equipment_id),
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
) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE workout_set SET reps=?, duration_sec=?, equipment_id=? WHERE id=?",
        (reps, duration_sec, equipment_id, set_id),
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
    from datetime import date, timedelta

    week_start, week_end = get_week_range()
    today = date.today()

    rows = (
        get_connection()
        .execute(
            """
            SELECT mg.id, mg.name, mg.weekly_sets,
                   COUNT(ws.id) AS completed_sets,
                   MAX(ws.date) AS last_trained
            FROM muscle_group mg
            LEFT JOIN exercise_muscle_group emg ON emg.muscle_group_id = mg.id
            LEFT JOIN exercise e ON e.id = emg.exercise_id
            LEFT JOIN workout_set ws ON ws.exercise_id = e.id
                AND ws.date >= ? AND ws.date <= ?
            GROUP BY mg.id, mg.name, mg.weekly_sets
            ORDER BY mg.name
            """,
            (week_start, week_end),
        )
        .fetchall()
    )

    try:
        rest_days_setting = int(get_setting("rest_days", "0"))
    except ValueError:
        rest_days_setting = 0

    muscle_groups = []
    for r in rows:
        rest_remaining: Optional[int] = None
        if rest_days_setting > 0 and r["last_trained"]:
            last_trained = date.fromisoformat(r["last_trained"])
            elapsed = (today - last_trained).days
            remaining = rest_days_setting - elapsed
            if remaining > 0:
                rest_remaining = remaining
        mg = MuscleGroup(
            id=r["id"],
            name=r["name"],
            weekly_sets=r["weekly_sets"],
            completed_sets=r["completed_sets"],
            rest_days_remaining=rest_remaining,
        )
        muscle_groups.append(mg)

    def sort_key(mg: MuscleGroup) -> tuple:
        resting = mg.rest_days_remaining is not None and mg.rest_days_remaining > 0
        if resting:
            # Resting groups: sink to bottom, sorted by most days remaining first
            return (2, mg.rest_days_remaining, mg.name)
        if mg.weekly_sets is None or mg.weekly_sets == 0:
            # No plan — after active groups but before resting
            return (1, 0, mg.name)
        ratio = mg.completed_sets / mg.weekly_sets
        return (0, ratio, mg.name)

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


def get_last_value_for_exercise(exercise_id: int) -> Optional[int]:
    """Return the most recent reps or duration_sec for *exercise_id*, or None."""
    row = (
        get_connection()
        .execute(
            """SELECT reps, duration_sec FROM workout_set
           WHERE exercise_id = ?
           ORDER BY date DESC, order_index DESC, created_at DESC
           LIMIT 1""",
            (exercise_id,),
        )
        .fetchone()
    )
    if row is None:
        return None
    return row["reps"] if row["reps"] is not None else row["duration_sec"]


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------


def export_all_data() -> dict:
    """Serialize all user data to a plain dict suitable for JSON serialisation."""
    conn = get_connection()
    muscle_groups = [
        dict(r)
        for r in conn.execute(
            "SELECT id, name, weekly_sets FROM muscle_group ORDER BY id"
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
                      duration_sec, equipment_id, created_at
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
    conn = get_connection()
    conn.execute("DELETE FROM workout_set")
    conn.execute("DELETE FROM exercise_muscle_group")
    conn.execute("DELETE FROM exercise")
    conn.execute("DELETE FROM equipment")
    conn.execute("DELETE FROM muscle_group")
    conn.commit()


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
            "INSERT INTO muscle_group(id, name, weekly_sets) VALUES (?, ?, ?)",
            (mg["id"], mg["name"], mg.get("weekly_sets")),
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
               (id, date, exercise_id, order_index, reps, duration_sec, equipment_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ws["id"],
                ws["date"],
                ws["exercise_id"],
                ws["order_index"],
                ws.get("reps"),
                ws.get("duration_sec"),
                ws.get("equipment_id"),
                ws.get("created_at", ""),
            ),
        )
    conn.commit()

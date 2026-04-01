"""CRUD helpers for all entities."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class Equipment:
    id: int
    name: str


@dataclass
class Exercise:
    id: int
    name: str
    muscle_group_id: int
    type: str  # 'reps' | 'time'
    muscle_group_name: str = ""


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
    rows = get_connection().execute(
        "SELECT id, name, weekly_sets FROM muscle_group ORDER BY name"
    ).fetchall()
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
    rows = get_connection().execute(
        "SELECT id, name FROM equipment ORDER BY name"
    ).fetchall()
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
# Exercise
# ---------------------------------------------------------------------------

def get_all_exercises() -> list[Exercise]:
    rows = get_connection().execute("""
        SELECT e.id, e.name, e.muscle_group_id, e.type, mg.name AS muscle_group_name
        FROM exercise e
        JOIN muscle_group mg ON mg.id = e.muscle_group_id
        ORDER BY e.name
    """).fetchall()
    return [Exercise(**dict(r)) for r in rows]


def get_exercises_by_muscle_group(mg_id: int) -> list[Exercise]:
    rows = get_connection().execute("""
        SELECT e.id, e.name, e.muscle_group_id, e.type, mg.name AS muscle_group_name
        FROM exercise e
        JOIN muscle_group mg ON mg.id = e.muscle_group_id
        WHERE e.muscle_group_id = ?
        ORDER BY e.name
    """, (mg_id,)).fetchall()
    return [Exercise(**dict(r)) for r in rows]


def create_exercise(name: str, muscle_group_id: int, ex_type: str) -> Exercise:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO exercise(name, muscle_group_id, type) VALUES (?, ?, ?)",
        (name, muscle_group_id, ex_type),
    )
    conn.commit()
    row = conn.execute("""
        SELECT e.id, e.name, e.muscle_group_id, e.type, mg.name AS muscle_group_name
        FROM exercise e JOIN muscle_group mg ON mg.id = e.muscle_group_id
        WHERE e.id = ?
    """, (cur.lastrowid,)).fetchone()
    return Exercise(**dict(row))


def update_exercise(ex_id: int, name: str, muscle_group_id: int, ex_type: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE exercise SET name=?, muscle_group_id=?, type=? WHERE id=?",
        (name, muscle_group_id, ex_type, ex_id),
    )
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
    rows = get_connection().execute("""
        SELECT ws.*, e.name AS exercise_name, e.type AS exercise_type,
               eq.name AS equipment_name
        FROM workout_set ws
        JOIN exercise e ON e.id = ws.exercise_id
        LEFT JOIN equipment eq ON eq.id = ws.equipment_id
        WHERE ws.date = ?
        ORDER BY ws.order_index, ws.created_at
    """, (date,)).fetchall()
    return [_row_to_workout_set(dict(r)) for r in rows]


def get_workout_dates() -> list[str]:
    """Return distinct workout dates in descending order."""
    rows = get_connection().execute(
        "SELECT DISTINCT date FROM workout_set ORDER BY date DESC"
    ).fetchall()
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
    row = conn.execute("""
        SELECT ws.*, e.name AS exercise_name, e.type AS exercise_type,
               eq.name AS equipment_name
        FROM workout_set ws
        JOIN exercise e ON e.id = ws.exercise_id
        LEFT JOIN equipment eq ON eq.id = ws.equipment_id
        WHERE ws.id = ?
    """, (cur.lastrowid,)).fetchone()
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

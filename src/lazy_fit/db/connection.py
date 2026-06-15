"""SQLite connection management and schema initialisation."""

import sqlite3
from pathlib import Path

_DB_PATH: Path | None = None
_conn: sqlite3.Connection | None = None


def set_db_path(path: Path) -> None:
    """Set the database file path (called once at app startup)."""
    global _DB_PATH
    _DB_PATH = path


def get_connection() -> sqlite3.Connection:
    """Return the shared SQLite connection, creating it if necessary."""
    global _conn
    if _conn is None:
        if _DB_PATH is None:
            raise RuntimeError("DB path not set. Call set_db_path() first.")
        _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def init_db() -> None:
    """Create all tables if they do not exist yet."""
    conn = get_connection()
    # Incremental migration: add columns introduced after initial release.
    try:
        conn.execute("ALTER TABLE muscle_group ADD COLUMN rest_days INTEGER")
        conn.commit()
    except Exception:
        pass  # column already exists
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS muscle_group (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            weekly_sets INTEGER,
            rest_days   INTEGER
        );

        CREATE TABLE IF NOT EXISTS equipment (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS exercise (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('reps', 'time'))
        );

        CREATE TABLE IF NOT EXISTS exercise_muscle_group (
            exercise_id     INTEGER NOT NULL REFERENCES exercise(id) ON DELETE CASCADE,
            muscle_group_id INTEGER NOT NULL REFERENCES muscle_group(id) ON DELETE CASCADE,
            PRIMARY KEY (exercise_id, muscle_group_id)
        );

        CREATE TABLE IF NOT EXISTS workout_set (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT NOT NULL,
            exercise_id  INTEGER NOT NULL REFERENCES exercise(id) ON DELETE CASCADE,
            order_index  INTEGER NOT NULL DEFAULT 0,
            reps         INTEGER,
            duration_sec INTEGER,
            equipment_id INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_workout_set_date ON workout_set(date);

        CREATE TABLE IF NOT EXISTS workout_set_equipment (
            set_id       INTEGER NOT NULL REFERENCES workout_set(id) ON DELETE CASCADE,
            equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
            PRIMARY KEY (set_id, equipment_id)
        );

        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    # One-time migration: copy existing workout_set.equipment_id into join table.
    try:
        rows = conn.execute(
            "SELECT id, equipment_id FROM workout_set WHERE equipment_id IS NOT NULL"
        ).fetchall()
        for row in rows:
            conn.execute(
                "INSERT OR IGNORE INTO workout_set_equipment(set_id, equipment_id) VALUES (?, ?)",
                (row[0], row[1]),
            )
        conn.commit()
    except Exception:
        pass

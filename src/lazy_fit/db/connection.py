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
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS muscle_group (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            weekly_sets INTEGER
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

        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()

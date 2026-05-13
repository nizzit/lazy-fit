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
    # Task 1.1 — add is_builtin flag to muscle_group
    try:
        conn.execute(
            "ALTER TABLE muscle_group ADD COLUMN is_builtin INTEGER NOT NULL DEFAULT 0"
        )
        conn.commit()
    except Exception:
        pass  # column already exists
    # Task 1.2 — add heart rate columns to workout_set
    try:
        conn.execute("ALTER TABLE workout_set ADD COLUMN avg_hr INTEGER")
        conn.commit()
    except Exception:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE workout_set ADD COLUMN max_hr INTEGER")
        conn.commit()
    except Exception:
        pass  # column already exists
    # Task 1.3 — migrate exercise table to support 'cardio' type
    try:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='exercise'"
        ).fetchone()
        if row and "'cardio'" not in row[0]:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.executescript("""
                CREATE TABLE exercise_new (
                    id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL CHECK(type IN ('reps', 'time', 'cardio'))
                );
                INSERT INTO exercise_new SELECT id, name, type FROM exercise;
                DROP TABLE exercise;
                ALTER TABLE exercise_new RENAME TO exercise;
            """)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()
    except Exception:
        pass
    # Add builtin_key column for translatable built-in group names
    try:
        conn.execute("ALTER TABLE muscle_group ADD COLUMN builtin_key TEXT")
        conn.commit()
    except Exception:
        pass  # column already exists
    # Backfill builtin_key for existing built-in groups (in case column was just added)
    try:
        conn.execute(
            "UPDATE muscle_group SET builtin_key='cardio_group_name' WHERE is_builtin=1 AND builtin_key IS NULL"
        )
        conn.commit()
    except Exception:
        pass
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS muscle_group (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            weekly_sets INTEGER,
            rest_days   INTEGER,
            is_builtin  INTEGER NOT NULL DEFAULT 0,
            builtin_key TEXT
        );



        CREATE TABLE IF NOT EXISTS equipment (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        -- Task 1.4 — include 'cardio' in CHECK for new databases
        CREATE TABLE IF NOT EXISTS exercise (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('reps', 'time', 'cardio'))
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
            avg_hr       INTEGER,
            max_hr       INTEGER,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_workout_set_date ON workout_set(date);

        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    # Task 1.5 — insert built-in cardio group if not present
    conn.execute(
        "INSERT OR IGNORE INTO muscle_group(name, is_builtin, builtin_key) VALUES ('cardio', 1, 'cardio_group_name')"
    )
    conn.commit()

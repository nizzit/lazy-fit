# AGENTS.md — Lazy Fit

Android workout tracker built with **Python 3.13 + Toga + Briefcase**. SQLite for local storage. Russian / English i18n.

---

## Commands

```bash
# Install dependencies
uv sync

# Run on desktop (fast iteration, no Android needed)
make dev          # equivalent: uv run python main.py

# Android (requires Java JDK + Android SDK with ANDROID_HOME set)
make create       # first-time scaffold: briefcase create android
make build        # compile APK: briefcase build android
make run          # install + launch on device/emulator
make package      # release APK: briefcase package android

# Stream Android logs
make logs         # adb logcat -s toga python

# Clean build artefacts
make clean
```

> There are **no tests** in this project. Desktop mode (`make dev`) is the fastest way to verify UI changes.

---

## Project Structure

```
lazy-fit/
├── main.py                         # Entry point → app.main()
├── pyproject.toml                  # Briefcase + project config
├── Makefile                        # Dev/build shortcuts
├── plans/architecture.md           # Detailed architecture doc
└── src/lazy_fit/
    ├── app.py                      # LazyFitApp (Toga App) + nav stack
    ├── widgets.py                  # StepperInput custom widget
    ├── db/
    │   ├── connection.py           # get_connection(), set_db_path(), init_db()
    │   └── models.py               # Dataclasses + CRUD for all entities
    ├── i18n/
    │   ├── __init__.py             # t(key), set_language(), get_language()
    │   ├── ru.py                   # Russian strings dict
    │   └── en.py                   # English strings dict
    └── screens/
        ├── home.py
        ├── muscle_groups.py
        ├── exercises.py
        ├── log_set.py              # Set logging + stopwatch timer + today's summary
        ├── history.py
        ├── workout_detail.py
        ├── edit_set.py
        ├── timer.py
        ├── _workout_log.py         # Shared display component (underscore = private module)
        └── settings/
            ├── __init__.py         # Settings menu + language toggle
            ├── manage_muscle_groups.py
            ├── manage_equipment.py
            ├── manage_exercises.py
            └── rest_timer.py
```

---

## Code Style

### Module structure

Every non-empty module opens with a single-line docstring using double quotes and an em-dash separator for multi-part descriptions:

```python
"""Log Set screen — record a set + show today's workout summary."""
```

Then `from __future__ import annotations` (required for PEP 563 with Python 3.13), then imports.

### Imports

Three blocks separated by blank lines — standard library, third-party, local:

```python
from __future__ import annotations

import sys
from datetime import date

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t
from lazy_fit.db.models import WorkoutSet, get_all_sets
```

**Screen-to-screen imports must be deferred** inside handler functions to avoid circular imports:

```python
def on_tap(widget: toga.Widget) -> None:
    from lazy_fit.screens.exercises import build as build_exercises
    app.nav_push(build_exercises(app), t("exercises"))
```

DB model imports used only inside handlers may also be deferred inside `build()`.

### Type annotations

All function signatures are fully annotated. Use `Optional[T]` (imported from `typing`) for nullable values. Use `list[T]` (lowercase) for list type hints:

```python
from typing import Callable, Optional

def build(app: toga.App, exercise: Optional[Exercise] = None) -> toga.Box: ...
def on_save(widget: toga.Widget) -> None: ...
```

Use `# type: ignore[<code>]` sparingly for unavoidable Toga callback type mismatches.

### Naming conventions

| Entity | Convention | Example |
|---|---|---|
| Functions / methods | `snake_case` | `get_all_exercises` |
| Classes | `PascalCase` | `LazyFitApp`, `WorkoutSet` |
| Event handlers | `on_<action>` | `on_save`, `on_delete` |
| Private helpers | `_name` prefix | `_refresh`, `_add_row` |
| Mutable closure refs | `<name>_ref` suffix | `value_input_ref` |
| Module-level globals | `_UPPER` or `_lower` | `_DB_PATH`, `_conn`, `_lang` |
| DB CRUD functions | `get_all_<entity>`, `create_<entity>`, `update_<entity>`, `delete_<entity>` | |
| Private modules | `_name.py` | `_workout_log.py` |

### Screen pattern

Every screen exports exactly one public function `build(app, ...) -> toga.Box`. Helper functions use `_` prefix:

```python
def build(app: toga.App) -> toga.Box:
    def on_something(widget: toga.Widget) -> None:
        from lazy_fit.screens.other import build as build_other
        app.nav_push(build_other(app), t("title_key"))

    def _refresh() -> None:
        ...

    root = toga.Box(children=[...], style=Pack(direction=COLUMN, flex=1))
    return root
```

### Mutable closure state

Use a single-element list for any variable that must be mutated by inner functions:

```python
timer_running = [False]
elapsed = [0]
input_ref: list[Optional[toga.NumberInput]] = [None]
```

### Layout / Pack

Use `Pack(...)` inline via `style=`. Common patterns:

- Root container: `Pack(direction=COLUMN, flex=1)`
- Form row: `Pack(direction=ROW, margin=4)`
- Expanding input/label: `Pack(flex=1, margin=4)`
- Form label: `Pack(margin=4, width=120)`
- Action button: `Pack(margin=8, width=240)`

### SQL

Multi-line SQL in triple-quoted strings, `?` placeholders, uppercase keywords:

```python
conn.execute(
    """
    SELECT * FROM workout_set
    WHERE date = ?
    ORDER BY order_index
    """,
    (today,),
)
```

### Error handling

- Inline validation: set `error_label.text = t("error_...")` and `return` early.
- Numeric conversions: catch `(ValueError, TypeError)` and fall back to a safe default.
- Platform fallbacks (Android wake lock, screen size): use bare `except Exception` with a silent fallback.
- Destructive actions: use async confirm dialog pattern via `app.add_background_task`.
- Raise `RuntimeError` for programming errors (e.g., calling `get_connection()` before `set_db_path()`).
- No logging except `logging.getLogger("lazy_fit")` in `timer.py` for Android-specific paths.

---

## Architecture

### Navigation

Toga has no built-in router. `LazyFitApp` in `app.py` implements a manual push/pop stack:

```python
app.nav_push(widget, title)          # push new screen
app.nav_pop()                        # go back
app.nav_replace_root(widget, title)  # replace entire stack (used after language switch)
```

The back button is injected automatically by `_render_current()` in `app.py` when the stack has more than one entry — **do not add your own back buttons** in screens.

### Database

Single shared SQLite connection managed in `db/connection.py`:

- `set_db_path(path)` — called once in `app.startup()` before anything else
- `get_connection()` — returns the global connection; raises if path not set
- `init_db()` — creates tables via `CREATE TABLE IF NOT EXISTS`; safe to call multiple times
- `row_factory = sqlite3.Row` — rows are dict-accessible (`r["column"]`)
- Foreign keys are enabled: `PRAGMA foreign_keys = ON`
- On Android, DB lives in `app.paths.data / "lazyfit.db"`; on desktop, same path under the OS data dir

All CRUD lives in `db/models.py` as plain functions (no ORM). Each entity has a corresponding `@dataclass`.

### i18n

```python
from lazy_fit.i18n import t, set_language, get_language

t("key")                  # returns translated string, falls back to key
set_language("ru")        # or "en"
get_language()            # returns current lang code
```

Language change requires rebuilding the UI — handled via `app.nav_replace_root(build_home(app), t("app_name"))` in the settings screen. Default language is `"ru"`.

**Adding a new string**: add it to both `i18n/ru.py` and `i18n/en.py` under the `strings` dict.

### Android-specific code

Guarded with `sys.platform != "android"` checks. The wake lock in `log_set.py` uses `jnius.autoclass` to call Android Java APIs — this import only works inside a Briefcase-packaged app, not on desktop.

---

## Data Model

| Table | Key columns |
|---|---|
| `muscle_group` | id, name (UNIQUE), weekly_sets (nullable) |
| `equipment` | id, name (UNIQUE) |
| `exercise` | id, name (UNIQUE), muscle_group_id FK, type `'reps'|'time'` |
| `workout_set` | id, date (ISO YYYY-MM-DD), exercise_id FK, order_index, reps, duration_sec, equipment_id FK (nullable) |

A **workout** is the logical grouping of all `workout_set` rows sharing the same `date`. No separate Workout table exists.

Cascade deletes: deleting a `muscle_group` cascades to `exercise`, which cascades to `workout_set`.

---

## Gotchas

- **No hot-reload**: each code change on desktop requires re-running `make dev`. Android builds are slow — iterate on desktop first.
- **`from __future__ import annotations`** is used in all modules — required for PEP 563 deferred evaluation with Python 3.13.
- **Deferred imports**: always import other screens inside handler functions, not at module top level, to avoid circular import issues.
- **Mutable closure state**: use `value = [initial]` (single-element list) when inner functions need to mutate the variable. See `timer_running`, `timer_elapsed`, `*_ref` vars in `log_set.py`.
- **Language switch rebuilds root**: `set_language()` alone does not update the UI — you must rebuild screens. The settings screen handles this with `nav_replace_root`.
- **SQLite on Android**: the DB path must be set via `set_db_path()` before any query. On desktop, the data directory auto-creates; on Android, `self.paths.data` provides the correct sandboxed path.
- **`sqlite3.Row` dict access**: use `dict(row)` to unpack rows into dataclass constructors, or access by column name `row["name"]`.
- **`check_same_thread=False`**: the SQLite connection allows cross-thread access — Toga background tasks run on different threads.
- **Ruff**: present in the environment (`uv run ruff`) but no `[tool.ruff]` config committed — runs with defaults. Add `# noqa: E402` only for post-`sys.path`-manipulation imports (as in `main.py`).

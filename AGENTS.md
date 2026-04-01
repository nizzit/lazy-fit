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
make run-android  # build + install + launch on device/emulator
make install      # build + install only (no launch)
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
        └── settings/
            ├── __init__.py         # Settings menu + language toggle
            ├── manage_muscle_groups.py
            ├── manage_equipment.py
            └── manage_exercises.py
```

---

## Architecture

### Navigation

Toga has no built-in router. `LazyFitApp` in `app.py` implements a manual push/pop stack:

```python
app.nav_push(widget, title)       # push new screen
app.nav_pop()                     # go back
app.nav_replace_root(widget, title)  # replace entire stack (used after language switch)
```

Every screen is a `build(app) -> toga.Box` factory function (some take extra args like `build(app, exercise)`). The `app` reference is threaded through all screens so they can call navigation methods.

### Screen pattern

```python
def build(app: toga.App) -> toga.Box:
    def on_something(widget: toga.Widget) -> None:
        from lazy_fit.screens.other import build as build_other
        app.nav_push(build_other(app), t("title_key"))

    root = toga.Box(children=[...], style=Pack(direction=COLUMN, flex=1))
    return root
```

- Imports of other screens are **deferred inside handlers** (inside functions), not at module top-level — this avoids circular imports and speeds up startup.
- Mutable state inside a screen is stored in `list` of one element (e.g., `timer_running = [False]`), a common Python closure workaround for mutating variables from inner functions.

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

## Toga / UI Conventions

- Layout uses `Pack` from `toga.style.pack` — `direction=COLUMN|ROW`, `flex=1`, `margin`, `align_items`
- `toga.ScrollContainer` wraps scrollable lists
- `toga.Selection` is used for dropdowns (equipment picker)
- `toga.NumberInput` for numeric inputs (reps / duration)
- Buttons for navigation and actions — no swipe gestures (Toga limitation)
- The back button is injected automatically by `_render_current()` in `app.py` when the stack has more than one entry — **don't add your own back buttons** in screens

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

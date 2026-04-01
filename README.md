# Lazy Fit — Workout Tracker

Android workout tracking app built with **Python 3.13 + Toga + Briefcase**.

## Features

- Record workout sets (reps or timed) with optional equipment
- Stopwatch timer for timed exercises (auto-fills duration)
- Today's workout summary grouped by exercise on the log screen
- Full workout history with per-set editing and deletion
- Reference data management: muscle groups, equipment, exercises
- Russian / English UI with runtime language toggle

## Project Structure

```
src/lazy_fit/
├── app.py                          # Toga App + push/pop navigation
├── db/
│   ├── connection.py               # SQLite init
│   └── models.py                   # CRUD for all entities
├── i18n/
│   ├── __init__.py                 # t(key) helper
│   ├── ru.py                       # Russian strings
│   └── en.py                       # English strings
└── screens/
    ├── home.py                     # Home screen
    ├── muscle_groups.py            # Muscle group list
    ├── exercises.py                # Exercise list (filtered)
    ├── log_set.py                  # Log set + timer + today's history
    ├── history.py                  # Workout history list
    ├── workout_detail.py           # Single workout (editable)
    ├── edit_set.py                 # Edit a single set
    └── settings/
        ├── __init__.py             # Settings menu
        ├── manage_muscle_groups.py
        ├── manage_equipment.py
        └── manage_exercises.py
```

## Running Locally (desktop)

```bash
# Install dependencies
uv sync

# Run on desktop (for quick testing)
python main.py
```

## Building for Android

```bash
# Install Briefcase
uv run briefcase create android
uv run briefcase build android
uv run briefcase run android
```

Or to build a release APK:

```bash
uv run briefcase package android
```

## Data Model

| Table | Fields |
|---|---|
| `muscle_group` | id, name, weekly_sets (opt.) |
| `equipment` | id, name |
| `exercise` | id, name, muscle_group_id, type (reps/time) |
| `workout_set` | id, date, exercise_id, order_index, reps, duration_sec, equipment_id |

A **workout** = all `workout_set` rows sharing the same `date` (ISO YYYY-MM-DD).

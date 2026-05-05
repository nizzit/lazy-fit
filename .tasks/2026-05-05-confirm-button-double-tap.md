# Confirm Button: Double-Tap Instead of Dialog

## Description
Заменить все диалоги подтверждения при удалении и сбросе данных на паттерн «двойного нажатия»:
при первом нажатии кнопка меняет текст на вопрос-подтверждение и подсвечивается более ярким
опасным цветом; при повторном нажатии действие выполняется. Если второго нажатия не
последует в течение таймаута (~3 сек), кнопка «остывает» и возвращается в исходное состояние.

## Motivation
Нативные диалоги `ConfirmDialog` выглядят чужеродно на Android и требуют двух отдельных
взаимодействий с системным попапом. Инлайн-подтверждение на самой кнопке — быстрее, нагляднее
и более уместно в мобильном UX. Паттерн применяется во многих мобильных приложениях.

## Scope
**В scope:**
- Создать переиспользуемый виджет/хелпер `ConfirmButton` в `widgets.py`.
- Заменить все `ConfirmDialog` для **удаления** и **сброса данных** на `ConfirmButton`.
- Добавить i18n-строки для состояния ожидания подтверждения.

**Вне scope:**
- `ImportDialog` (import_confirm) — там требуется объяснение последствий, диалог уместен.
- `ExportDialog` и информационные диалоги (`InfoDialog`) — не затрагиваем.
- Диалог подтверждения импорта — оставляем как есть.

## Project Context

### Conventions to follow
- `from __future__ import annotations` первой строкой в модуле.
- Хелпер-класс/функция — `PascalCase` для класса, `snake_case` для функций.
- Мутируемое состояние в замыканиях — `state = [initial]`.
- `themed_pack(**kwargs)` для стилей (None-значения отбрасываются).
- `COLOR_BTN_DANGER()` — текущий danger-цвет (`#ff80ab`); для «активированного» состояния
  нужен более яркий: `#ff4081` (уже есть в палитре как `"diff_down"` / `"error"`).
- Цвета на Android only — `_IS_ANDROID` guard; на десктопе None → нативные.
- Таймер через `app.add_background_task` + `asyncio.sleep` или через `threading.Timer`.
- Деferred-импорты screen→screen внутри хендлеров.
- Нет hot-reload — проверяем через `make dev`.

### Affected files (likely)
- `src/lazy_fit/widgets.py` — добавить `ConfirmButton`
- `src/lazy_fit/ui_constants.py` — добавить `COLOR_BTN_DANGER_ACTIVE()` (яркий розовый)
- `src/lazy_fit/i18n/ru.py` — добавить строки `"confirm_action"` / контекстные
- `src/lazy_fit/i18n/en.py` — то же
- `src/lazy_fit/screens/edit_set.py` — заменить `on_delete` с диалогом
- `src/lazy_fit/screens/workout_detail.py` — заменить `on_delete` (подход) и `on_delete_workout`
- `src/lazy_fit/screens/history.py` — заменить `on_delete_workout`
- `src/lazy_fit/screens/settings/_crud.py` — заменить кнопку delete в `build_entity_form`
- `src/lazy_fit/screens/settings/manage_exercises.py` — заменить `on_delete`
- `src/lazy_fit/screens/settings/manage_muscle_groups.py` — заменить `on_delete`
- `src/lazy_fit/screens/settings/manage_equipment.py` — заменить `on_delete`
- `src/lazy_fit/screens/settings/data.py` — заменить `on_reset` (сброс данных)
- `pyproject.toml` — bump версии PATCH (0.5.3 → 0.5.4)

### Notes
- `toga.Button` не имеет прямого `.text` setter в некоторых бэкендах — нужно проверить API.
  Toga Button имеет атрибут `text` (read/write). Если не работает — пересоздавать кнопку нельзя
  (нет replace в box), поэтому можно хранить `label_ref` внутри `ConfirmButton` и обновлять
  его через `button.text = ...`.
- Таймаут сброса: 3 секунды — достаточно для обдуманного нажатия, не слишком долго.
- `ConfirmButton` должен быть `toga.Button` подкласс или обёртка. Поскольку Toga Box нельзя
  заменить в середине layout, лучше сделать класс-наследник `toga.Button` который сам
  управляет своим состоянием.
- Для таймера: `app.add_background_task(async lambda...)` — стандартный паттерн проекта.
  Нужен `app` ref внутри виджета, либо передавать `app` в метод активации.
- Состояния: `idle` → `pending` (первый тап, старт таймера) → `idle` (таймаут или второй тап).
- `on_press` callback у `toga.Button` задаётся при создании и через `.on_press` setter.
  `ConfirmButton` должен перехватывать нажатия своим внутренним хендлером и вызывать
  `action` только при втором нажатии.

## Acceptance Criteria
- [x] `ConfirmButton` реализован в `widgets.py`: принимает `text`, `confirm_text`, `action`, `app`, стили
- [x] Первое нажатие: кнопка меняет текст на `confirm_text`, цвет на ярко-розовый (`COLOR_BTN_DANGER_ACTIVE`)
- [x] Второе нажатие (в течение 3 сек): вызывается `action(widget)`, кнопка возвращается в idle
- [x] Таймаут 3 сек без второго нажатия: кнопка возвращается в idle-состояние (текст + цвет)
- [x] Все `ConfirmDialog` для delete/reset заменены на `ConfirmButton`
- [x] `import_confirm` диалог оставлен без изменений
- [x] i18n строки добавлены в ru.py и en.py
- [x] Версия bumped до 0.5.4

## Implementation Plan
1. Добавить `COLOR_BTN_DANGER_ACTIVE()` в `ui_constants.py` → `#ff4081` на Android, None на десктоп.
2. Добавить i18n строки: `"delete_confirm"` (ru: `"Точно удалить?"`, en: `"Sure? Tap again"`) и  `"reset_confirm_btn"` (ru: `"Точно сбросить?"`, en: `"Sure? Tap again"`).
3. Реализовать `ConfirmButton(toga.Button)` в `widgets.py`:
   - `__init__(text, confirm_text, action, app, **style_kwargs)`
   - Внутренние поля: `_idle_text`, `_confirm_text`, `_action`, `_app`, `_pending = [False]`
   - Переопределить `on_press` → `_handle_press`
   - `_handle_press`: если `_pending[0]` → вызвать `_action`, сброс; иначе → активировать
   - `_activate()`: `self.text = _confirm_text`, сменить цвет, `_pending[0] = True`, запустить таймер
   - `_deactivate()`: восстановить текст и цвет, `_pending[0] = False`
   - Таймер: `app.add_background_task` с `asyncio.sleep(3)` → `_deactivate()` если ещё pending
4. Заменить delete-кнопки в `_crud.py::build_entity_form` — `on_delete` передаётся как `action`.
5. Заменить в `edit_set.py` — убрать `async on_delete`, создать `ConfirmButton`.
6. Заменить в `workout_detail.py` — обе кнопки удаления (подход + вся тренировка).
7. Заменить в `history.py` — кнопка удаления тренировки.
8. Заменить в `settings/manage_exercises.py`, `manage_muscle_groups.py`, `manage_equipment.py` — убрать async диалоги, передать голый `on_delete` action в `_crud.py` (который теперь оборачивает в ConfirmButton).
9. Заменить `on_reset` в `settings/data.py`.
10. Bump версии в `pyproject.toml`: `0.5.3 → 0.5.4`.
11. Проверить `make dev` — убедиться что десктоп запускается без ошибок.

## Completed
Date: 2026-05-05
Changes: Implemented ConfirmButton double-tap pattern; replaced all delete/reset ConfirmDialogs; added COLOR_BTN_DANGER_ACTIVE; added i18n keys; bumped version to 0.5.4
Files changed:
- src/lazy_fit/ui_constants.py
- src/lazy_fit/widgets.py
- src/lazy_fit/i18n/ru.py
- src/lazy_fit/i18n/en.py
- src/lazy_fit/screens/edit_set.py
- src/lazy_fit/screens/workout_detail.py
- src/lazy_fit/screens/history.py
- src/lazy_fit/screens/settings/_crud.py
- src/lazy_fit/screens/settings/manage_exercises.py
- src/lazy_fit/screens/settings/manage_muscle_groups.py
- src/lazy_fit/screens/settings/manage_equipment.py
- src/lazy_fit/screens/settings/data.py
- pyproject.toml

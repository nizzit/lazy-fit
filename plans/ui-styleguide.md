# UI Style Guide — LazyFit

> Документ охватывает: аудит текущего состояния (визуальный + UX), единый стайлгайд и план приведения интерфейса.

---

## Часть 0. UX-аудит — сохранение, удаление, навигация

### 0.1 Сводная таблица паттернов сохранения

| Экран | Паттерн сохранения | Поведение после Save | Кнопка Cancel |
|---|---|---|---|
| `log_set.py` | Явная кнопка "Сохранить подход" | **Остаётся на экране** | нет |
| `edit_set.py` | Явные Save + Cancel + Delete | `nav_pop()` | да |
| `manage_muscle_groups` — форма | Явные Save + Cancel + Delete | `nav_pop()` | да |
| `manage_equipment` — форма | Явные Save + Cancel + Delete | `nav_pop()` | да |
| `manage_exercises` — форма | Явные Save + Cancel + Delete | `nav_pop()` | да |
| `rest_timer.py` | **Авто-сохранение** при каждом on_change | остаётся | нет |
| `training_period.py` | **Авто-сохранение** при каждом on_change | остаётся | нет |
| `settings/__init__.py` — язык | **Немедленное** применение + пересборка UI | полный reset стека | нет |
| `history.py` | нет формы | — | — |
| `workout_detail.py` | нет формы | — | — |
| `data.py` | нет формы (диалоги ОС) | — | — |

**Проблема:** два принципиально разных подхода к сохранению без видимого критерия выбора между ними.

---

### 0.2 Сводная таблица паттернов удаления

| Место | Confirmation dialog | Тип удаляемого объекта | Cascade-риск |
|---|---|---|---|
| `history.py` — кнопка в строке | **ДА** | Workout (весь день) | высокий |
| `workout_detail.py` — кнопка Delete workout | **ДА** | Workout (весь день) | высокий |
| `workout_detail.py` — кнопка Delete set | **ДА** | Один подход | низкий |
| `edit_set.py` — кнопка Delete | **НЕТ** | Один подход | низкий |
| `manage_muscle_groups` — список | **НЕТ** | MuscleGroup → cascade на exercises + sets | **критический** |
| `manage_muscle_groups` — форма | **НЕТ** | MuscleGroup → cascade на exercises + sets | **критический** |
| `manage_equipment` — список | **НЕТ** | Equipment | низкий |
| `manage_equipment` — форма | **НЕТ** | Equipment | низкий |
| `manage_exercises` — список | **НЕТ** | Exercise → cascade на sets | средний |
| `manage_exercises` — форма | **НЕТ** | Exercise → cascade на sets | средний |
| `data.py` — Reset | **ДА** | Все данные приложения | критический |

**Проблема:** удаление MuscleGroup удаляет каскадом все упражнения и все подходы этой группы — **без единого предупреждения**. Аналогично для Exercise.

---

### 0.3 Детальный разбор несогласованностей

#### UX-1: Авто-сохранение vs явное сохранение

`rest_timer.py` и `training_period.py` вызывают `set_setting()` прямо в `on_change` каждого виджета. Пользователь не видит момента сохранения. Если он случайно нажал +/− и передумал — нет кнопки "Отмена".

Все CRUD-экраны (manage_*) требуют явного Save. Пользователь может нажать Back и данные **молча потеряются** — форма не предупреждает.

Итог: пользователь не знает, когда данные сохраняются, а когда — нет.

#### UX-2: Кнопка Delete прямо в строке списка (manage_*)

```
[ Жим штанги лёжа ]  [ Удалить ]
```

На мобильном экране кнопки вплотную. Промах пальцем → немедленное каскадное удаление упражнения со всеми подходами. Нет возможности отменить.

#### UX-3: Поведение Back на форме CRUD

Пользователь открывает форму редактирования группы мышц, меняет название, нажимает системную кнопку Back (не Cancel). Данные теряются молча. В `edit_set.py` та же ситуация.

#### UX-4: Delete в edit_set без подтверждения

`edit_set.py:on_delete` удаляет подход без ConfirmDialog. При этом `workout_detail.py:_add_set_row.on_delete` для того же объекта показывает ConfirmDialog. Один сет — два разных поведения удаления в зависимости от пути навигации.

#### UX-5: log_set — Save не уходит назад (намеренно, но неочевидно)

Пользователь нажимает "Сохранить подход" и остаётся на том же экране. Это правильно (несколько подходов подряд), но нет никакого визуального подтверждения что подход сохранён — кроме появления строки в истории ниже.

#### UX-7: manage_* — Delete в списке дублирует Delete в форме

Каждая строка CRUD-списка имеет кнопку Delete. Нажатие Edit открывает форму, где тоже есть Delete. Два пути к одному действию, оба без confirmation.

---

### 0.4 Что работает правильно

- `history.py` и `workout_detail.py` — Delete с ConfirmDialog. Образец для остальных
- `data.py` — Reset с ConfirmDialog + информационный диалог после успеха
- `log_set.py` — Save без nav_pop() оправдан контекстом (серийная запись подходов)
- `edit_set.py` — Save + Cancel + Delete в одном месте, структура понятна

---

### 0.5 Единый UX-стандарт

#### Категория A: экраны-настройки (не объекты)

**Когда использовать:** настройки, которые применяются мгновенно и легко обратимы (переключатель on/off, выбор режима).

**Паттерн:** авто-сохранение при изменении. Нет Save/Cancel.

**Применяется к:** `rest_timer.py` (Switch), `training_period.py` (Switch для режима недели).

**Исключение — числовые поля (StepperInput):** авто-сохранение при on_change тоже допустимо, т.к. шаг атомарен и значение всегда валидно. Пользователь видит текущее значение.

---

#### Категория B: CRUD-объекты

**Когда использовать:** создание/редактирование именованных объектов (упражнение, группа мышц, оборудование, подход).

**Паттерн:**
1. Форма открывается через `nav_push()`
2. Кнопки: **[Сохранить]** `flex=1` · **[Отмена]** `flex=1` · **[Удалить]** (только при редактировании, без flex)
3. Сохранить → валидация → DB → `refresh_fn()` → `nav_pop()`
4. Отмена → `nav_pop()` (без сохранения)
5. Удалить → **ConfirmDialog** → DB → `refresh_fn()` → `nav_pop()`

**Применяется к:** manage_*, edit_set.

---

#### Категория C: запись действия (log_set)

**Паттерн:**
1. Явная кнопка **[Сохранить подход]** — без `nav_pop()`, экран остаётся
2. Визуальное подтверждение — запись мгновенно появляется в истории под формой
3. Нет Cancel (нечего отменять — форма всегда показывает последнее записанное значение)

---

#### Удаление — единое правило

| Сценарий | Confirmation | Причина |
|---|---|---|
| Удалить MuscleGroup | **ВСЕГДА** | cascade на exercises + sets |
| Удалить Exercise | **ВСЕГДА** | cascade на sets |
| Удалить Workout (день) | **ВСЕГДА** | много данных |
| Удалить Equipment | нет | нет каскада, низкий риск |
| Удалить WorkoutSet | нет | единичная запись, легко добавить снова |

**Текст confirm-диалога** должен указывать что именно будет удалено каскадом:
```
"Удалить группу мышц «Грудь»? Будут удалены все упражнения и подходы этой группы."
```

---

#### Удаление из строки списка — убрать кнопку Delete

Кнопка Delete непосредственно в строке списка (рядом с именем) — опасна на мобильном. Единственный путь к удалению объекта — через форму редактирования.

**До:**
```
[ Жим штанги лёжа (кнопка-edit) ]  [ Удалить ]
```

**После:**
```
[ Жим штанги лёжа (кнопка-edit) ]
```

Это требует изменения `_crud.py:build_list_row` — убрать `on_delete` из строки.

---

#### Переключение языка — предупреждение

Перед `nav_replace_root` добавить `ConfirmDialog`:
```
"Переключить язык? Текущий экран будет закрыт."
```

---

### 0.6 Итоговая таблица UX-изменений

| # | Файл | Изменение | Приоритет |
|---|---|---|---|
| U1 | `screens/settings/_crud.py` | Убрать кнопку Delete из строки списка | высокий |
| U2 | `screens/settings/manage_muscle_groups.py` | ConfirmDialog на Delete (форма) с текстом о cascade | высокий |
| U3 | `screens/settings/manage_exercises.py` | ConfirmDialog на Delete (форма) с текстом о cascade | высокий |
| U4 | `screens/settings/manage_equipment.py` | ConfirmDialog на Delete (форма) — по единому правилу | средний |
| U5 | `screens/edit_set.py` | ConfirmDialog на Delete | средний |
| U7 | `screens/log_set.py` | Визуальное подтверждение сохранения (flash-сообщение или анимация) | низкий |

---

## Часть 1. Аудит текущего состояния

### 1.1 Ширины кнопок — несогласованность

Кнопки в приложении используют три разных подхода к ширине без очевидной системы:

| Экран | Стиль кнопки | Значение |
|---|---|---|
| `home.py` | `width=240, margin=12` | фиксированная 240 |
| `settings/__init__.py` | `width=280, margin=12` | фиксированная 280 |
| `settings/data.py` | `width=280, margin=12` | фиксированная 280 |
| `muscle_groups.py` | `flex=1, margin=8` | растягивается |
| `exercises.py` | `flex=1, margin=8` | растягивается |
| `timer.py` | `width=160` | фиксированная 160 |
| `_workout_log.py` | `width=64, margin=4` | мини-кнопка |
| `_crud.py` (add btn) | `margin=8` | без ширины/flex |
| `_crud.py` (list row edit) | `flex=1, margin=4` | растягивается |
| `edit_set.py` | `margin=8` | без ширины/flex |
| `log_set.py` (save) | `margin=12` | без ширины/flex |
| `history.py` (delete) | `margin=(8, 8, 2, 8)` | нестандартный отступ |
| `workout_detail.py` (edit/del) | `margin=4` | без ширины/flex |

**Проблема:** Home и Settings дают разную ширину (240 vs 280) для визуально одинаковых меню. Кнопки Save/Cancel/Delete в формах не согласованы между экранами.

---

### 1.2 Ширина меток форм — два значения

| Экран | Ширина метки |
|---|---|
| `log_set.py`, `edit_set.py` | `width=120` |
| `_crud.py` (build_form_field), `manage_exercises.py` | `width=140` |
| `rest_timer.py` (flex=1 на label) | растягивается |
| `training_period.py` (flex=1 на label) | растягивается |

**Проблема:** Поля форм выровнены по-разному в зависимости от экрана. `rest_timer.py` и `training_period.py` вовсе используют вертикальный стек (COLUMN) вместо стандартного ROW-паттерна.

---

### 1.3 Отступы корневого контейнера

| Экран | Отступ root |
|---|---|
| `home.py`, `settings/__init__.py` | `margin=32, align_items="center"` |
| `edit_set.py`, `_crud.py` (form), `training_period.py`, `rest_timer.py` | `margin=16` |
| `log_set.py` (form_box) | `margin=8` |
| `history.py`, `muscle_groups.py`, `exercises.py` | без margin на root |

**Проблема:** Три разных значения margin для схожих по типу экранов.

---

### 1.4 Шрифты — нет единой шкалы

| Место | font_size |
|---|---|
| `timer.py` — время | `64` |
| `timer.py` — заголовок | `18` |
| `log_set.py` — заголовок упражнения | `16` |
| `log_set.py` — заголовок истории | `14` |
| `history.py` — дата | `15` |
| `workout_detail.py` — упражнение | `14` |
| `_workout_log.py` — упражнение | `13` |
| `training_period.py` — секция | `bold` (нет size) |

**Проблема:** Используются 5 уникальных размеров (13-16-18-64) + `font_weight="bold"` без размера. Нет системы "заголовок / подзаголовок / текст".

---

### 1.5 Экраны без прокрутки

Следующие экраны рендерят фиксированный `Box` без `ScrollContainer`. На маленьких экранах (или при большом количестве контента) часть UI обрежется:

- `edit_set.py` — форма редактирования подхода
- `settings/rest_timer.py` — настройки таймера
- `settings/training_period.py` — настройки периода тренировок
- `settings/__init__.py` — меню настроек
- `settings/data.py` — управление данными
- `home.py` — главный экран

---

### 1.6 Единственный hardcoded цвет

В `app.py:122` — `background_color="#66bb6a"` для баннера таймера. Нигде больше цвета не задаются явно. Нет константы, нет системы цветов.

---

### 1.7 Layout паттерны в `rest_timer.py` и `training_period.py`

Эти два экрана используют нестандартный паттерн для полей с `StepperInput`:

```python
# rest_timer.py — нестандартно
toga.Box(
    children=[
        toga.Box(children=[toga.Label(t("rest_timer_duration"), ...)], direction=ROW),
        toga.Box(children=[toga.Box(flex=1), duration_input], direction=ROW),
    ],
    style=Pack(direction=COLUMN),
)
```

Вместо стандартного:

```python
# build_form_field — стандартно
toga.Box(
    children=[toga.Label(t("..."), width=140), stepper_input],
    style=Pack(direction=ROW, margin=4),
)
```

Это создаёт дополнительный уровень вложенности и выглядит иначе, чем CRUD-формы.

---

### 1.8 Деструктивные кнопки не выделены визуально

Кнопки "Удалить" выглядят идентично "Сохранить" и "Отмена". Визуального предупреждения нет нигде.

---

### 1.9 Что работает хорошо (не трогать)

- Паттерн пустого состояния — `toga.Label(t("..."), Pack(margin=16))` — везде одинаков
- `ScrollContainer(flex=1)` в списковых экранах — консистентен
- `_crud.py` — хорошо инкапсулирует паттерн CRUD
- `StepperInput` — правильно инкапсулирует Android-специфику
- `_workout_log.py` — grid-паттерн с расчётом `per_row` по ширине экрана
- Деferred imports в хендлерах — везде соблюдаются

---

## Часть 2. Единый стайлгайд

### 2.1 Шкала отступов

Базовая единица — **4px**. Допустимые значения:

| Токен | Значение | Применение |
|---|---|---|
| `SPACE_XS` | `4` | отступ внутри виджета (margin для Label/Button в строке) |
| `SPACE_SM` | `8` | отступ строки в списке, кнопка в строке действий |
| `SPACE_MD` | `16` | отступ секции, margin form-контейнера |
| `SPACE_LG` | `32` | отступ меню-экранов (Home, Settings, Data) |

Нестандартные значения (`margin=12`, `margin=(8, 8, 2, 8)`) удалить.

---

### 2.2 Шкала шрифтов

| Токен | Значение | Применение |
|---|---|---|
| `FONT_XL` | `48` | таймер (крупный дисплей времени) |
| `FONT_LG` | `18` | заголовок экрана / header таймера |
| `FONT_MD` | `15` | секционный заголовок с `font_weight="bold"` |
| `FONT_SM` | `13` | вторичный текст (упражнение в лог-строке) |
| `FONT_BASE` | (системный) | всё остальное — не задавать `font_size` явно |

Значения `16`, `14`, `13` в разных контекстах → унифицировать по токенам выше.

---

### 2.3 Ширины

| Токен | Значение | Применение |
|---|---|---|
| `FORM_LABEL_W` | `128` | ширина метки в строке формы (унификация 120/140) |
| `BTN_MENU_W` | `280` | кнопки главного меню и меню настроек |
| `BTN_TIMER_W` | `160` | кнопка таймера |
| `BTN_SET_W` | `64` | мини-кнопка подхода в workout log |

Кнопки в формах (Save/Cancel/Delete) и в списках — **без фиксированной ширины**, только `flex=1` или `margin=SPACE_SM`.

---

### 2.4 Паттерны компоновки

#### Экран-меню (Home, Settings, Data)

```python
toga.Box(
    children=[...buttons...],
    style=Pack(direction=COLUMN, align_items="center", margin=SPACE_LG, flex=1),
)
```
Кнопки: `Pack(width=BTN_MENU_W, margin=SPACE_SM)`.

#### Прокручиваемый список

```python
scroll_content = toga.Box(style=Pack(direction=COLUMN))
# ... add rows ...
scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
root = toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))
```

Применяется для **всех** экранов с переменным количеством элементов, включая формы.

#### Строка формы (label + input)

```python
toga.Box(
    children=[
        toga.Label(t(key), style=Pack(margin=SPACE_XS, width=FORM_LABEL_W)),
        widget,  # flex=1, margin=SPACE_XS
    ],
    style=Pack(direction=ROW, margin=SPACE_XS),
)
```

Используется для TextInput, NumberInput, StepperInput, Selection.

#### Строка переключателя (label + Switch)

```python
toga.Box(
    children=[
        toga.Label(t(key), style=Pack(margin=SPACE_XS, flex=1)),
        toga.Switch("", value=..., style=Pack(margin_left=SPACE_SM)),
    ],
    style=Pack(direction=ROW, margin=SPACE_XS),
)
```

#### Строка кнопок действий формы

```python
toga.Box(
    children=[save_btn, cancel_btn],         # delete_btn — только если применимо
    style=Pack(direction=ROW, margin=SPACE_SM),
)
```

Кнопки: `Pack(flex=1, margin=SPACE_SM)` — каждая занимает равную долю строки.  
**Исключение:** кнопка Delete — `Pack(margin=SPACE_SM)` без `flex` (меньшая, справа).

#### Строка в списке (name + action buttons)

```python
toga.Box(
    children=[
        toga.Button(name, on_press=on_edit, style=Pack(flex=1, margin=SPACE_XS)),
        toga.Button(t("delete"), on_press=on_delete, style=Pack(margin=SPACE_XS)),
    ],
    style=Pack(direction=ROW, margin=SPACE_XS),
)
```

#### Секция с заголовком

```python
toga.Box(
    children=[
        toga.Label(t(title_key), style=Pack(margin=SPACE_XS, font_size=FONT_MD, font_weight="bold")),
        row1,
        row2,
    ],
    style=Pack(direction=COLUMN, margin_bottom=SPACE_MD),
)
```

---

### 2.5 Константы (`src/lazy_fit/ui_constants.py`)

Вынести все magic numbers в один файл:

```python
"""UI layout constants."""

# Spacing
SPACE_XS: int = 4
SPACE_SM: int = 8
SPACE_MD: int = 16
SPACE_LG: int = 32

# Font sizes
FONT_XL: int = 48   # timer display
FONT_LG: int = 18   # screen header / timer context label
FONT_MD: int = 15   # section title
FONT_SM: int = 13   # secondary text

# Widths
FORM_LABEL_W: int = 128
BTN_MENU_W: int = 280
BTN_TIMER_W: int = 160
BTN_SET_W: int = 64

# Colors
COLOR_TIMER_BANNER: str = "#66bb6a"
```

---

### 2.6 Обновить `_crud.py` — единая точка для CRUD-паттернов

`build_form_field` использовать с `width=FORM_LABEL_W` вместо `width=140`.  
`build_entity_form` — кнопки Save/Cancel с `flex=1`, Delete без `flex`.

---

### 2.7 Правила для форм с `StepperInput`

`rest_timer.py` и `training_period.py` должны использовать стандартную строку формы:

```python
build_form_field("rest_timer_duration", duration_input)
```

Вместо нестандартного двухуровневого COLUMN-паттерна.

---

### 2.8 Прокрутка везде

Все экраны-формы (edit_set, rest_timer, training_period, manage_*) должны оборачиваться в `ScrollContainer`. Реализовать через вспомогательную функцию:

```python
# в _crud.py или shared helpers
def wrap_scroll(widget: toga.Widget) -> toga.Box:
    scroll = toga.ScrollContainer(content=widget, style=Pack(flex=1))
    return toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))
```

---

## Часть 3. План приведения интерфейса под стайлгайд

### Приоритет 1 — Создать `ui_constants.py` (основа всего)

**Файл:** `src/lazy_fit/ui_constants.py`  
**Действие:** Создать с константами из раздела 2.5.  
**Риск:** нулевой — только новый файл, ничего не ломает.

---

### Приоритет 2 — Обновить `_crud.py` (затрагивает 3 CRUD-экрана)

**Файл:** `src/lazy_fit/screens/settings/_crud.py`

| Изменение | До | После |
|---|---|---|
| `build_form_field` label width | `width=140` | `width=FORM_LABEL_W` (128) |
| `build_entity_form` кнопки Save/Cancel | `margin=8` | `flex=1, margin=SPACE_SM` |
| `build_entity_form` кнопка Delete | `margin=8` | `margin=SPACE_SM` (без flex) |
| `build_crud_screen` add btn | `margin=8` | `margin=SPACE_SM` |

Затрагивает: `manage_muscle_groups.py`, `manage_equipment.py`, `manage_exercises.py`.

---

### Приоритет 3 — Унифицировать кнопки главного меню

**Файл:** `src/lazy_fit/screens/home.py`

| Изменение | До | После |
|---|---|---|
| `btn_style` width | `width=240` | `width=BTN_MENU_W` (280) |
| `btn_style` margin | `margin=12` | `margin=SPACE_SM` |
| `root` margin | `margin=32` | `margin=SPACE_LG` |

---

### Приоритет 4 — Переписать `rest_timer.py` на стандартный паттерн

**Файл:** `src/lazy_fit/screens/settings/rest_timer.py`

| Изменение | До | После |
|---|---|---|
| Layout duration/delay | COLUMN с двумя вложенными ROW | `build_form_field(key, stepper)` |
| toggle_row label style | `flex=1` | `flex=1` (оставить — Switch-паттерн) |
| root margin | `margin=16` | `margin=SPACE_MD` |
| Прокрутка | нет | `wrap_scroll(form_box)` |

---

### Приоритет 5 — Переписать `training_period.py` на стандартный паттерн

**Файл:** `src/lazy_fit/screens/settings/training_period.py`

| Изменение | До | После |
|---|---|---|
| Layout `_limit_row` | COLUMN с двумя ROW | `build_form_field(key, stepper)` |
| Секция заголовки | `font_weight="bold"` без size | `font_size=FONT_MD, font_weight="bold"` |
| root margin | `margin=16` | `margin=SPACE_MD` |
| Прокрутка | нет | `wrap_scroll(box)` |

---

### Приоритет 6 — Унифицировать `log_set.py`

**Файл:** `src/lazy_fit/screens/log_set.py`

| Изменение | До | После |
|---|---|---|
| `input_label` width | `width=120` | `width=FORM_LABEL_W` |
| `save_btn` style | `margin=12` | `Pack(flex=1, margin=SPACE_SM)` |
| `header` font_size | `16` | `FONT_LG` (18) |
| `history_title` font_size | `14` | `FONT_MD` (15) |
| `history_title` margin | `(12, 8, 4, 8)` | `Pack(margin=SPACE_SM, font_size=FONT_MD)` |

---

### Приоритет 7 — Унифицировать `edit_set.py`

**Файл:** `src/lazy_fit/screens/edit_set.py`

| Изменение | До | После |
|---|---|---|
| `input_label` width | `width=120` | `width=FORM_LABEL_W` |
| `save_btn`/`cancel_btn` | `margin=8` | `flex=1, margin=SPACE_SM` |
| `delete_btn` | `margin=8` | `margin=SPACE_SM` (без flex) |
| root margin | `margin=16` | `margin=SPACE_MD` |
| Прокрутка | нет | `wrap_scroll(root)` |

---

### Приоритет 8 — Шрифты в `_workout_log.py` и `history.py`

**Файл:** `src/lazy_fit/screens/_workout_log.py`

| Изменение | До | После |
|---|---|---|
| exercise label font_size | `13` | `FONT_SM` |

**Файл:** `src/lazy_fit/screens/history.py`

| Изменение | До | После |
|---|---|---|
| date label font_size | `15` | `FONT_MD` |
| date label margin | `(12, 8, 2, 8)` | `Pack(margin=SPACE_SM, ...)` |
| delete btn margin | `(8, 8, 2, 8)` | `margin=SPACE_SM` |

---

### Приоритет 9 — `workout_detail.py`

**Файл:** `src/lazy_fit/screens/workout_detail.py`

| Изменение | До | После |
|---|---|---|
| exercise label font_size | `14` | `FONT_MD` (15) |
| exercise label margin | `(8, 8, 2, 8)` | `margin=SPACE_SM` |
| set row margin | `(2, 8)` | `margin=SPACE_XS` |

---

### Приоритет 10 — `timer.py`

**Файл:** `src/lazy_fit/screens/timer.py`

| Изменение | До | После |
|---|---|---|
| time_label font_size | `64` | `FONT_XL` (48) |
| header label font_size | `18` | `FONT_LG` |
| stop_btn width | `width=160` | `width=BTN_TIMER_W` |

---

### Приоритет 11 — `app.py` баннер

**Файл:** `src/lazy_fit/app.py`

| Изменение | До | После |
|---|---|---|
| banner `background_color` | `"#66bb6a"` | `COLOR_TIMER_BANNER` |
| banner `width=120` | `120` | хардкод (оставить — специфика) |

---

### Что НЕ трогать

- `StepperInput` в `widgets.py` — уже хорошо
- Деferred imports — уже консистентны
- Паттерн пустого состояния — уже консистентен
- Grid `_workout_log.py` + `_buttons_per_row` — специфическая логика
- Логика навигации в `app.py`

---

## Итоговая таблица изменений

### Визуальные изменения (стайлгайд)

| Приоритет | Файл(ы) | Тип изменения | Риск |
|---|---|---|---|
| V1 | `ui_constants.py` (новый) | создать | нет |
| V2 | `screens/settings/_crud.py` | рефакторинг кнопок, label width | низкий |
| V3 | `screens/home.py` | margin + width | низкий |
| V4 | `screens/settings/rest_timer.py` | layout + scroll | средний |
| V5 | `screens/settings/training_period.py` | layout + scroll | средний |
| V6 | `screens/log_set.py` | margin + font + label width | низкий |
| V7 | `screens/edit_set.py` | margin + label width + scroll | низкий |
| V8 | `screens/_workout_log.py`, `history.py` | font + margin | низкий |
| V9 | `screens/workout_detail.py` | font + margin | низкий |
| V10 | `screens/timer.py` | font + width | низкий |
| V11 | `app.py` | извлечь цветовую константу | нет |

### UX-изменения (паттерны сохранения и удаления)

| Приоритет | Файл(ы) | Тип изменения | Риск |
|---|---|---|---|
| U1 | `screens/settings/_crud.py` | Убрать Delete из строки списка | **высокий** — меняет привычный поток |
| U2 | `screens/settings/manage_muscle_groups.py` | ConfirmDialog на Delete с текстом о cascade | высокий |
| U3 | `screens/settings/manage_exercises.py` | ConfirmDialog на Delete с текстом о cascade | высокий |
| U4 | `screens/settings/manage_equipment.py` | ConfirmDialog на Delete | средний |
| U5 | `screens/edit_set.py` | ConfirmDialog на Delete | средний |
| U6 | `screens/settings/__init__.py` | ConfirmDialog перед сменой языка | низкий |
| U7 | `screens/log_set.py` | Визуальный flash после сохранения подхода | низкий |

### Зависимости между задачами

```
V1 (ui_constants.py)  ──► все V2–V11
U1 (_crud.py)         ──► U2, U3, U4 (форма получает единственный путь к Delete)
V2 (_crud.py)         ──► U1          (обе задачи трогают _crud.py — делать вместе)
```

### Рекомендуемый порядок выполнения

1. **V1** — создать `ui_constants.py`
2. **V2 + U1** — рефакторинг `_crud.py` (визуал + убрать Delete из списка)
3. **U2 + U3 + U4** — ConfirmDialog в manage-формах (делать вместе)
4. **V3** — `home.py`
5. **V4 + V5** — `rest_timer.py`, `training_period.py`
6. **V6 + U5** — `log_set.py` + `edit_set.py`
7. **V7** — `edit_set.py` scroll
8. **V8, V9, V10, V11** — точечные правки шрифтов и отступов
9. **U7** — log_set feedback

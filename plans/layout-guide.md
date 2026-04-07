# Layout Guide — Lazy Fit

Toga использует движок **Pack** (аналог Flexbox). Все экраны строятся из вложенных `toga.Box` с `style=Pack(...)`.

---

## Основные оси

| Параметр | Значение |
|---|---|
| `direction=COLUMN` | дети идут сверху вниз (вертикальный стек) |
| `direction=ROW` | дети идут слева направо (горизонтальная строка) |

Если `direction` не задан — по умолчанию `ROW`.

---

## flex

`flex=1` заставляет виджет занять всё доступное пространство по главной оси родителя.

```
ROW  + flex=1 → тянется по ширине
COLUMN + flex=1 → тянется по высоте
```

Правило: **хотя бы один дочерний элемент** в строке/колонке должен иметь `flex=1`, иначе содержимое не растянется.

---

## Отступы (margin)

```python
margin=4            # одно значение — все 4 стороны
margin=(12, 8, 4, 8)  # top, right, bottom, left (как CSS)
margin_left=8       # одна сторона
```

---

## Ширина / высота

```python
width=120    # фиксированная ширина
width=240    # стандартная ширина кнопок действий
width=64     # мини-кнопки (счётчики подходов)
width=96     # StepperInput в настройках
```

---

## Типовые паттерны

### 1. Экран-список (прокручиваемый)

```
toga.Box  direction=COLUMN, flex=1          ← root
  └─ toga.ScrollContainer  flex=1
       └─ toga.Box  direction=COLUMN        ← scroll_content (контент)
            ├─ row1
            ├─ row2
            └─ ...
```

Применяется в: `history.py`, `muscle_groups.py`, `_crud.py` (build_crud_screen).

```python
scroll_content = toga.Box(style=Pack(direction=COLUMN, flex=1))
# ... добавляем дочерние элементы ...
scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
root = toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))
return root
```

---

### 2. Форма (фиксированный контент без скролла)

```
toga.Box  direction=COLUMN, margin=16       ← root
  ├─ field-row
  ├─ field-row
  ├─ error_label
  └─ btn-row
```

Применяется в: `edit_set.py`, `_crud.py` (build_entity_form), `rest_timer.py`, `training_period.py`.

```python
return toga.Box(
    children=[input_row, equip_row, btn_row],
    style=Pack(direction=COLUMN, margin=16),
)
```

---

### 3. Строка формы (label + input)

```
toga.Box  direction=ROW, margin=4
  ├─ toga.Label  width=120–160, margin=4   ← фиксированная ширина
  └─ input/stepper/selection  flex=1, margin=4  ← растягивается
```

Паттерн: метка фиксированной ширины слева, контрол растягивается:

```python
toga.Box(
    children=[
        toga.Label(t("reps"), style=Pack(margin=4, width=120)),
        value_input,   # flex=1
    ],
    style=Pack(direction=ROW, margin=4),
)
```

Ширина метки: `width=120` (короткие), `width=140` (средние), `width=160` (длинные).  
Хелпер `build_form_field(label_key, widget)` в `_crud.py` инкапсулирует этот паттерн с `width=140`.

---

### 4. Строка «переключатель» (label + Switch)

Switch не растягивается — метка получает `flex=1`, Switch имеет `margin_left=8`:

```python
toga.Box(
    children=[
        toga.Label(t("some_option"), style=Pack(margin=4, flex=1)),
        toga.Switch("", value=..., on_change=..., style=Pack(margin_left=8)),
    ],
    style=Pack(direction=ROW, margin=4),
)
```

---

### 5. Строка кнопок действий

```
toga.Box  direction=ROW, margin=8
  ├─ Button "Сохранить"  margin=8
  ├─ Button "Отмена"     margin=8
  └─ Button "Удалить"    margin=8  (опционально)
```

```python
toga.Box(
    children=[save_btn, cancel_btn, delete_btn],
    style=Pack(direction=ROW, margin=8),
)
```

---

### 6. Центрированные кнопки на домашнем экране

```
toga.Box  direction=COLUMN, align_items="center", margin=32, flex=1
  ├─ Button  width=240, margin=12
  └─ Button  width=240, margin=12
```

---

### 7. Секции с заголовком

```
toga.Box  direction=COLUMN                  ← section-box
  ├─ toga.Label  font_weight="bold", margin=4   ← заголовок секции
  ├─ field-row
  └─ field-row
```

Секции объединяются в корневой `COLUMN`-контейнер с `margin=16`.

---

### 8. Форма со скроллом (длинный контент)

```
toga.Box  direction=COLUMN, flex=1          ← root
  └─ toga.ScrollContainer  flex=1
       └─ toga.Box  direction=COLUMN        ← scroll_content
            ├─ header_label
            ├─ form_box
            ├─ section_title
            └─ log_box
```

Применяется в `log_set.py`.

---

## Виджеты и их типовые стили

| Виджет | Типовой стиль |
|---|---|
| `toga.Label` (заголовок секции) | `Pack(margin=4, font_weight="bold")` |
| `toga.Label` (метка поля) | `Pack(margin=4, width=120)` или `width=140/160` |
| `toga.Label` (растягиваемый) | `Pack(margin=4, flex=1)` |
| `toga.Label` (заголовок экрана) | `Pack(margin=8, font_size=16)` |
| `toga.Button` (действие) | `Pack(margin=8, width=240)` |
| `toga.Button` (список) | `Pack(flex=1, margin=4)` |
| `toga.Button` (в строке) | `Pack(margin=8)` |
| `toga.Button` (мини) | `Pack(margin=4, width=64)` |
| `toga.Switch` | `Pack(margin_left=8)` |
| `toga.Selection` | `Pack(flex=1, margin=4)` |
| `toga.TextInput` | `Pack(flex=1, margin=4)` |
| `toga.NumberInput` | `Pack(flex=1, margin=4)` |
| `StepperInput` | `Pack(width=160, margin=4)` — всегда фиксированная ширина; на Android внутри три элемента (input + 2 кнопки по 48px), `flex=1` перекроет Label |
| `toga.ScrollContainer` | `Pack(flex=1)` |

---

## Типовые ошибки

| Проблема | Причина | Решение |
|---|---|---|
| Контент не растягивается | Нет `flex=1` в цепочке | Добавить `flex=1` каждому контейнеру до root |
| Элемент не скроллится | `ScrollContainer` без `flex=1` | Добавить `Pack(flex=1)` |
| Label не выравнивается с input | Нет фиксированной ширины у label | `width=120/140/160` |
| Switch «прыгает» на весь ROW | `flex=1` попал на Switch | `flex=1` должен быть у Label, не Switch |
| Форма слипается с краями | Нет `margin` на root | `margin=16` на корневом Box |

---

## Примеры из кода

### Строка формы (edit_set.py)
```python
toga.Box(
    children=[
        toga.Label(t(label_key), style=Pack(margin=4, width=120)),
        value_input,  # StepperInput, flex=1
    ],
    style=Pack(direction=ROW, margin=4),
)
```

### Переключатель (rest_timer.py)
```python
toga.Box(
    children=[
        toga.Label(t("rest_timer_on"), style=Pack(margin=4, width=160)),
        rest_switch,   # Pack(margin_left=8)
    ],
    style=Pack(direction=ROW, margin=4),
)
```

### Секция с заголовком (training_period.py)
```python
toga.Box(
    children=[
        toga.Label(t("section_title"), style=Pack(margin=4, font_weight="bold")),
        field_row_1,
        field_row_2,
    ],
    style=Pack(direction=COLUMN),
)
```

### Скроллируемый список (_crud.py)
```python
scroll_content = toga.Box(
    children=[add_btn, list_box],
    style=Pack(direction=COLUMN),
)
scroll = toga.ScrollContainer(content=scroll_content, style=Pack(flex=1))
return toga.Box(children=[scroll], style=Pack(direction=COLUMN, flex=1))
```

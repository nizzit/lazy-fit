"""Equipment picker widget — chip-strip + '+' dropdown for multi-select."""

from __future__ import annotations

from typing import Callable, Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.db.models import Equipment
from lazy_fit.ui_constants import (
    COLOR_BTN_ADD,
    COLOR_BTN_DANGER,
    COLOR_BTN_DANGER_ACTIVE,
    COLOR_BTN_SECONDARY,
    SPACE_XS,
    themed_pack,
)


def build_equipment_picker(
    equipment_list: list[Equipment],
    initial_ids: list[int],
    on_change: Callable[[list[int]], None],
    app: toga.App,
) -> toga.Box:
    """Return a self-contained equipment picker Box.

    Layout (no equipment selected):
        [+]

    Layout (some selected):
        [Штанга] [Скамья] [+]   ← chips + add button (ROW)
        [Гиря]                   ← dropdown, shown only while open
        ...

    First tap on a chip turns it red (confirm state).
    Second tap removes it.
    Tap on [+] opens/closes the dropdown of remaining items.
    *on_change* is called with the current ID list on every change.
    """

    selected_ids: list[int] = list(initial_ids)
    dropdown_open: list[bool] = [False]

    chips_row_ref: list[Optional[toga.Box]] = [None]
    dropdown_box_ref: list[Optional[toga.Box]] = [None]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _eq_name(eq_id: int) -> str:
        for eq in equipment_list:
            if eq.id == eq_id:
                return eq.name
        return str(eq_id)

    def _available() -> list[Equipment]:
        return [eq for eq in equipment_list if eq.id not in selected_ids]

    def _close_dropdown() -> None:
        dropdown_open[0] = False
        dd = dropdown_box_ref[0]
        if dd is None:
            return
        for child in list(dd.children):
            dd.remove(child)

    def _rebuild_dropdown() -> None:
        dd = dropdown_box_ref[0]
        if dd is None:
            return
        for child in list(dd.children):
            dd.remove(child)
        avail = _available()
        if not avail:
            dropdown_open[0] = False
            return
        for eq in avail:
            eq_id_cap = eq.id

            def _make_add(eid: int) -> object:
                def on_add(widget: toga.Widget) -> None:
                    selected_ids.append(eid)
                    _close_dropdown()
                    _rebuild_chips()
                    on_change(list(selected_ids))
                return on_add

            dd.add(
                toga.Button(
                    eq.name,
                    on_press=_make_add(eq_id_cap),
                    style=themed_pack(
                        flex=1,
                        margin=SPACE_XS,
                        background_color=COLOR_BTN_SECONDARY(),
                    ),
                )
            )

    def _rebuild_chips() -> None:
        row = chips_row_ref[0]
        if row is None:
            return
        for child in list(row.children):
            row.remove(child)

        for eq_id in selected_ids:
            row.add(_make_chip(eq_id))

        # [+] button — square, same size as set log buttons
        if _available():
            def on_add_pressed(widget: toga.Widget) -> None:
                if dropdown_open[0]:
                    _close_dropdown()
                else:
                    dropdown_open[0] = True
                    _rebuild_dropdown()

            add_btn = toga.Button(
                "+",
                on_press=on_add_pressed,
                style=themed_pack(
                    width=48,
                    height=48,
                    margin=SPACE_XS,
                    background_color=COLOR_BTN_ADD(),
                ),
            )
            row.add(add_btn)

    def _make_chip(eq_id: int) -> toga.Button:
        """Return a chip button with double-tap-to-remove behaviour."""
        idle_color = COLOR_BTN_SECONDARY()
        danger_color = COLOR_BTN_DANGER()
        danger_active = COLOR_BTN_DANGER_ACTIVE()
        pending: list[bool] = [False]
        name = _eq_name(eq_id)

        btn: list[Optional[toga.Button]] = [None]

        def _deactivate() -> None:
            pending[0] = False
            b = btn[0]
            if b is None:
                return
            b.text = f"{name} ×"
            if idle_color is not None:
                b.style.background_color = idle_color
            elif danger_color is not None:
                b.style.background_color = None  # type: ignore[assignment]

        def _activate() -> None:
            pending[0] = True
            b = btn[0]
            if b is None:
                return
            if danger_color is not None:
                b.style.background_color = danger_color
            elif danger_active is not None:
                b.style.background_color = danger_active

            async def _wait_and_reset(_sender: object) -> None:
                import asyncio
                await asyncio.sleep(3.0)
                if pending[0]:
                    _deactivate()

            app.add_background_task(_wait_and_reset)

        def on_press(widget: toga.Widget) -> None:
            if pending[0]:
                # Second tap — confirm remove
                pending[0] = False
                if eq_id in selected_ids:
                    selected_ids.remove(eq_id)
                _close_dropdown()
                _rebuild_chips()
                on_change(list(selected_ids))
            else:
                _activate()

        b = toga.Button(
            f"{name} ×",
            on_press=on_press,
            style=themed_pack(
                margin=SPACE_XS,
                background_color=idle_color,
            ),
        )
        btn[0] = b
        return b

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    chips_row = toga.Box(style=Pack(direction=ROW, margin_bottom=SPACE_XS))
    chips_row_ref[0] = chips_row

    dropdown_box = toga.Box(style=Pack(direction=COLUMN))
    dropdown_box_ref[0] = dropdown_box

    _rebuild_chips()

    return toga.Box(
        children=[chips_row, dropdown_box],
        style=Pack(direction=COLUMN),
    )

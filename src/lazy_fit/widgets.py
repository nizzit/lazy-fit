"""Shared custom widgets."""

from __future__ import annotations

import sys

import toga
from toga.style import Pack
from toga.style.pack import ROW

from lazy_fit.ui_constants import COLOR_BTN_PRIMARY, COLOR_BTN_DANGER, COLOR_BTN_DANGER_ACTIVE, STEPPER_INPUT_W, themed_pack


class ConfirmButton(toga.Button):
    """Button that requires a double-tap to execute a destructive action.

    First tap: switches to confirm state (different text + danger-active colour).
    Second tap within *timeout* seconds: calls *action(widget)*.
    No second tap: reverts to idle after *timeout* seconds.
    """

    def __init__(
        self,
        text: str,
        action: object,
        app: toga.App,
        timeout: float = 3.0,
        **style_kwargs: object,
    ) -> None:
        self._idle_text = text
        self._action = action
        self._app = app
        self._timeout = timeout
        self._pending: list[bool] = [False]
        self._idle_color = COLOR_BTN_DANGER()
        self._active_color = COLOR_BTN_DANGER_ACTIVE()
        super().__init__(
            text,
            on_press=self._handle_press,
            style=themed_pack(**style_kwargs),
        )

    def _handle_press(self, widget: toga.Widget) -> None:
        if self._pending[0]:
            # Second tap — execute action and reset
            self._pending[0] = False
            self._deactivate()
            self._action(widget)  # type: ignore[operator]
        else:
            self._activate()

    def _activate(self) -> None:
        self._pending[0] = True
        if self._active_color is not None:
            self.style.background_color = self._active_color

        async def _wait_and_reset(_sender: object) -> None:
            import asyncio

            await asyncio.sleep(self._timeout)
            if self._pending[0]:
                self._pending[0] = False
                self._deactivate()

        self._app.add_background_task(_wait_and_reset)

    def _deactivate(self) -> None:
        if self._idle_color is not None:
            self.style.background_color = self._idle_color
        elif self._active_color is not None:
            # Reset to None (native) if no idle colour but active was set
            self.style.background_color = None  # type: ignore[assignment]


class StepperInput(toga.Box):
    """NumberInput with explicit −/+ buttons.

    On Android, toga.NumberInput has no built-in step buttons, so this
    widget wraps it with dedicated decrement/increment buttons.
    On all other platforms the buttons are omitted and the native spinner
    is used instead.
    """

    def __init__(
        self,
        *,
        min: float | None = None,
        max: float | None = None,
        step: float = 1,
        value: float = 0,
        style: Pack | None = None,
        on_change: object = None,
    ) -> None:
        self._step = step
        self._min = min
        self._max = max

        self._input = toga.NumberInput(
            min=min,
            max=max,
            step=step,
            value=value,
            on_change=on_change,
            style=Pack(width=STEPPER_INPUT_W),
        )

        if sys.platform == "android":
            minus_btn = toga.Button(
                "−",
                on_press=self._on_decrement,
                style=themed_pack(width=48, margin=2, background_color=COLOR_BTN_PRIMARY()),
            )
            plus_btn = toga.Button(
                "+",
                on_press=self._on_increment,
                style=themed_pack(width=48, margin=2, background_color=COLOR_BTN_PRIMARY()),
            )
            children: list[toga.Widget] = [self._input, minus_btn, plus_btn]
        else:
            children = [self._input]

        super().__init__(children=children, style=style or Pack())
        self.style.direction = ROW

    # ------------------------------------------------------------------
    @property
    def value(self) -> float | None:
        return self._input.value

    @value.setter
    def value(self, v: float | None) -> None:
        self._input.value = v

    # ------------------------------------------------------------------
    def _on_decrement(self, widget: toga.Widget) -> None:
        try:
            current = float(self._input.value or 0)
        except (TypeError, ValueError):
            current = 0.0
        new_val = current - self._step
        if self._min is not None:
            new_val = max(float(self._min), new_val)
        self._input.value = int(new_val) if self._step == int(self._step) else new_val

    def _on_increment(self, widget: toga.Widget) -> None:
        try:
            current = float(self._input.value or 0)
        except (TypeError, ValueError):
            current = 0.0
        new_val = current + self._step
        if self._max is not None:
            new_val = min(float(self._max), new_val)
        self._input.value = int(new_val) if self._step == int(self._step) else new_val

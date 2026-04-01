"""Shared custom widgets."""

from __future__ import annotations

import sys

import toga
from toga.style import Pack
from toga.style.pack import ROW


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
            style=Pack(flex=1),
        )

        if sys.platform == "android":
            minus_btn = toga.Button(
                "−",
                on_press=self._on_decrement,
                style=Pack(width=48, margin=2),
            )
            plus_btn = toga.Button(
                "+",
                on_press=self._on_increment,
                style=Pack(width=48, margin=2),
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

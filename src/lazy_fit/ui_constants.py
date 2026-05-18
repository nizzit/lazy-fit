"""UI layout constants — colours applied on Android only, native on other platforms."""

from __future__ import annotations

import sys
from typing import Optional

from toga.style import Pack

# Spacing
SPACE_XS: int = 4
SPACE_SM: int = 8
SPACE_MD: int = 16
SPACE_LG: int = 32

# Font sizes
FONT_XL: int = 48  # timer display
FONT_LG: int = 18  # screen header / timer context label
FONT_MD: int = 15  # section title
FONT_SM: int = 13  # secondary text
FONT_XS: int = 11  # diff badge / micro labels

# Widths
STEPPER_INPUT_W: int = 72
# Total width of a right-side input: StepperInput full width (with −/+ buttons on Android)
FORM_INPUT_W: int = (
    STEPPER_INPUT_W + 2 * 52 if sys.platform == "android" else STEPPER_INPUT_W
)
BTN_MENU_W: int = 280
BTN_TIMER_W: int = 160
BTN_TIMER_H: int = 88
BTN_SET_W: int = 64

# ---------------------------------------------------------------------------
# Colour palette — Android only.
# On other platforms theme_color() returns None so widgets keep native look.
# Palette: teal #26a69a (accent) · pink #ff4081 (danger)
# ---------------------------------------------------------------------------

_IS_ANDROID: bool = sys.platform == "android"

_PALETTE: dict[str, str] = {
    "btn_primary": "#b2dfdb",  # teal 100
    "btn_add": "#26a69a",  # teal 400
    "btn_disabled": "#bdbdbd",  # grey 400
    "btn_secondary": "#f5f5f5",  # grey 100
    "btn_danger": "#ff80ab",  # pink A100
    "btn_danger_active": "#ff4081",  # pink A200
    "diff_up": "#26a69a",  # teal 400
    "diff_down": "#ff4081",  # pink A200
    "error": "#ff4081",  # pink A200
}


def theme_color(key: str) -> Optional[str]:
    """Return colour for *key* on Android; None elsewhere (native OS colours)."""
    return _PALETTE[key] if _IS_ANDROID else None


# Shorthand accessors — call as functions: COLOR_BTN_PRIMARY()
def COLOR_BTN_PRIMARY() -> Optional[str]:
    return theme_color("btn_primary")  # noqa: N802


def COLOR_BTN_ADD() -> Optional[str]:
    return theme_color("btn_add")  # noqa: N802


def COLOR_BTN_SECONDARY() -> Optional[str]:
    return theme_color("btn_secondary")  # noqa: N802


def COLOR_BTN_DANGER() -> Optional[str]:
    return theme_color("btn_danger")  # noqa: N802


def COLOR_BTN_DISABLED() -> Optional[str]:
    return theme_color("btn_disabled")  # noqa: N802


def COLOR_BTN_DANGER_ACTIVE() -> Optional[str]:
    return theme_color("btn_danger_active")  # noqa: N802


def COLOR_DIFF_UP() -> Optional[str]:
    return theme_color("diff_up")  # noqa: N802


def COLOR_DIFF_DOWN() -> Optional[str]:
    return theme_color("diff_down")  # noqa: N802


def COLOR_ERROR() -> Optional[str]:
    return theme_color("error")  # noqa: N802


# ---------------------------------------------------------------------------
# Pack helper — builds Pack dropping any kwargs whose value is None.
#
#   themed_pack(margin=8, background_color=COLOR_BTN_PRIMARY())
#
# On non-Android COLOR_*() returns None → background_color omitted → native.
# ---------------------------------------------------------------------------


def themed_pack(**kwargs: object) -> Pack:
    """Return Pack(**kwargs) with None values removed."""
    return Pack(**{k: v for k, v in kwargs.items() if v is not None})

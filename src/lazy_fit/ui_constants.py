"""UI layout constants."""

import sys

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
STEPPER_INPUT_W: int = 72
# Total width of a right-side input: StepperInput full width (with −/+ buttons on Android)
FORM_INPUT_W: int = STEPPER_INPUT_W + 2 * 52 if sys.platform == "android" else STEPPER_INPUT_W
BTN_MENU_W: int = 280
BTN_TIMER_W: int = 160
BTN_SET_W: int = 64

# Colors
COLOR_TIMER_BANNER: str = "#66bb6a"

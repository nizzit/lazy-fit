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
FONT_XS: int = 11   # diff badge / micro labels

# Widths
STEPPER_INPUT_W: int = 72
# Total width of a right-side input: StepperInput full width (with −/+ buttons on Android)
FORM_INPUT_W: int = STEPPER_INPUT_W + 2 * 52 if sys.platform == "android" else STEPPER_INPUT_W
BTN_MENU_W: int = 280
BTN_TIMER_W: int = 160
BTN_SET_W: int = 64

# Colors
# Base palette: teal #26a69a (accent) · pink #ff4081 (danger)
COLOR_BTN_PRIMARY: str = "#b2dfdb"   # teal 100 — default button color
COLOR_BTN_ADD: str = "#26a69a"       # teal 400 — add / create action buttons
COLOR_BTN_SECONDARY: str = "#f5f5f5" # grey 100 — secondary buttons (back, cancel, resting)
COLOR_BTN_DANGER: str = "#ff80ab"    # pink A100 — destructive / danger buttons
COLOR_DIFF_UP: str = "#26a69a"       # teal 400 — set value improved vs previous
COLOR_DIFF_DOWN: str = "#ff4081"     # pink A200 — set value dropped vs previous
COLOR_ERROR: str = "#ff4081"         # pink A200 — inline validation error text

"""Settings root screen."""

from __future__ import annotations

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.i18n import t, set_language, get_language
from lazy_fit.db.models import set_setting
from lazy_fit.ui_constants import BTN_MENU_W, SPACE_SM, SPACE_LG, COLOR_BTN_PRIMARY, themed_pack


def build(app: toga.App) -> toga.Box:
    """Build and return the settings menu screen."""

    def on_muscle_groups(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings.manage_muscle_groups import build as b

        app.nav_push(b(app), t("manage_muscle_groups"))

    def on_equipment(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings.manage_equipment import build as b

        app.nav_push(b(app), t("manage_equipment"))

    def on_exercises(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings.manage_exercises import build as b

        app.nav_push(b(app), t("manage_exercises"))

    def on_rest_timer(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings.rest_timer import build as b

        app.nav_push(b(app), t("rest_timer"))

    def on_training_period(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings.training_period import build as b

        app.nav_push(b(app), t("training_period"))

    def on_data(widget: toga.Widget) -> None:
        from lazy_fit.screens.settings.data import build as b

        app.nav_push(b(app), t("data_management"))

    def on_lang_toggle(widget: toga.Widget) -> None:
        new_lang = "en" if get_language() == "ru" else "ru"
        set_language(new_lang)
        set_setting("language", new_lang)
        from lazy_fit.screens.home import build as build_home

        app.nav_replace_root(build_home(app), t("app_name"))
        app.nav_push(build(app), t("settings"))

    btn_style = themed_pack(margin=SPACE_SM, width=BTN_MENU_W, background_color=COLOR_BTN_PRIMARY())

    return toga.Box(
        children=[
            toga.Button(t("manage_muscle_groups"), on_press=on_muscle_groups, style=btn_style),
            toga.Button(t("manage_equipment"), on_press=on_equipment, style=btn_style),
            toga.Button(t("manage_exercises"), on_press=on_exercises, style=btn_style),
            toga.Button(t("rest_timer"), on_press=on_rest_timer, style=btn_style),
            toga.Button(t("training_period"), on_press=on_training_period, style=btn_style),
            toga.Button(t("data_management"), on_press=on_data, style=btn_style),
            toga.Button(t("lang_toggle"), on_press=on_lang_toggle, style=btn_style),
        ],
        style=Pack(direction=COLUMN, align_items="center", margin=SPACE_LG, flex=1),
    )

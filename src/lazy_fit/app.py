"""Main Toga application with a simple push/pop navigation stack."""

from __future__ import annotations

from pathlib import Path

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t, set_language
from lazy_fit.db.connection import set_db_path, init_db


class LazyFitApp(toga.App):
    """Workout tracker application."""

    def startup(self) -> None:
        # ------------------------------------------------------------------ DB
        data_dir = self.paths.data
        data_dir.mkdir(parents=True, exist_ok=True)
        set_db_path(data_dir / "lazyfit.db")
        init_db()

        # ------------------------------------------------------------------ i18n
        set_language("ru")

        # ------------------------------------------------------------------ nav stack
        # Each entry: (content_widget, title_str)
        self._nav_stack: list[tuple[toga.Widget, str]] = []

        # ------------------------------------------------------------------ main window
        self.main_window = toga.MainWindow(title=t("app_name"))

        # Build home and push it as root
        from lazy_fit.screens.home import build as build_home
        home = build_home(self)
        self._nav_stack = [(home, t("app_name"))]
        self._render_current()

        self.main_window.show()

    # ---------------------------------------------------------------------- navigation API

    def nav_push(self, widget: toga.Widget, title: str) -> None:
        """Push a new screen onto the navigation stack."""
        self._nav_stack.append((widget, title))
        self._render_current()

    def nav_pop(self) -> None:
        """Pop the top screen off the navigation stack."""
        if len(self._nav_stack) > 1:
            self._nav_stack.pop()
            self._render_current()

    def nav_replace_root(self, widget: toga.Widget, title: str) -> None:
        """Replace the entire stack with a single new root screen."""
        self._nav_stack = [(widget, title)]
        self._render_current()

    def _render_current(self) -> None:
        """Render the top-of-stack screen inside the main window."""
        content, title = self._nav_stack[-1]
        self.main_window.title = title

        can_go_back = len(self._nav_stack) > 1

        if can_go_back:
            back_btn = toga.Button(
                f"‹ {t('back')}",
                on_press=lambda w: self.nav_pop(),
                style=Pack(margin=4),
            )
            nav_bar = toga.Box(
                children=[back_btn],
                style=Pack(direction=ROW, margin=4),
            )
            wrapper = toga.Box(
                children=[nav_bar, content],
                style=Pack(direction=COLUMN, flex=1),
            )
        else:
            wrapper = toga.Box(
                children=[content],
                style=Pack(direction=COLUMN, flex=1),
            )

        self.main_window.content = wrapper


def main() -> LazyFitApp:
    return LazyFitApp(
        "Lazy Fit",
        "com.lazyfit.lazy_fit",
    )

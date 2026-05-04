"""Main Toga application with a simple push/pop navigation stack."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from lazy_fit.i18n import t, set_language
from lazy_fit.db.connection import set_db_path, init_db
from lazy_fit.db.models import get_setting
from lazy_fit.ui_constants import COLOR_BTN_DANGER, COLOR_BTN_SECONDARY, themed_pack


class LazyFitApp(toga.App):
    """Workout tracker application."""

    def startup(self) -> None:
        # ------------------------------------------------------------------ DB
        data_dir = self.paths.data
        data_dir.mkdir(parents=True, exist_ok=True)
        set_db_path(data_dir / "lazyfit.db")
        init_db()

        # ------------------------------------------------------------------ i18n
        set_language(get_setting("language", "ru"))

        # ------------------------------------------------------------------ active timer
        # Set by timer.py when a timer starts; cleared when it stops.
        # Structure: {running, elapsed, mode, wake_lock_ref, banner_label,
        #             banner_text, screen_widget, screen_title, minimize_fn}
        self.active_timer: Optional[dict] = None

        # ------------------------------------------------------------------ nav stack
        # Each entry: (content_widget, title_str, optional_back_fn, show_back)
        # optional_back_fn overrides the default nav_pop for that screen.
        # show_back=False hides the back button entirely.
        self._nav_stack: list[tuple[toga.Widget, str, Optional[Callable], bool, Optional[Callable[[], toga.Widget]]]] = []

        # ------------------------------------------------------------------ main window
        self.main_window = toga.MainWindow(title=t("app_name"))

        # Build home and push it as root
        from lazy_fit.screens.home import build as build_home

        home = build_home(self)
        self._nav_stack = [(home, t("app_name"), None, True, None)]
        self._render_current()

        self.main_window.show()

    # ---------------------------------------------------------------------- navigation API

    def nav_push(
        self,
        widget: toga.Widget,
        title: str,
        back_fn: Optional[Callable] = None,
        show_back: bool = True,
        refresh_fn: Optional[Callable[[], toga.Widget]] = None,
    ) -> None:
        """Push a new screen onto the navigation stack.

        refresh_fn, if provided, is called whenever the screen becomes the
        top of the stack again (e.g. after a child screen is popped) so the
        widget is always rebuilt with fresh data.
        """
        self._nav_stack.append((widget, title, back_fn, show_back, refresh_fn))
        self._render_current()

    def nav_pop(self) -> None:
        """Pop the top screen off the navigation stack."""
        if len(self._nav_stack) > 1:
            self._nav_stack.pop()
            if len(self._nav_stack) == 1:
                from lazy_fit.screens.home import build as build_home

                self._nav_stack[0] = (build_home(self), t("app_name"), None, True, None)
            else:
                # Rebuild the now-visible screen if it registered a refresh_fn.
                content, title, back_fn, show_back, refresh_fn = self._nav_stack[-1]
                if refresh_fn is not None:
                    self._nav_stack[-1] = (refresh_fn(), title, back_fn, show_back, refresh_fn)
            self._render_current()

    def nav_replace_root(self, widget: toga.Widget, title: str) -> None:
        """Replace the entire stack with a single new root screen."""
        self.cancel_active_timer()
        self._nav_stack = [(widget, title, None, True, None)]
        self._render_current()

    def restore_timer(self) -> None:
        """Re-push the minimised timer screen onto the nav stack."""
        if not self.active_timer:
            return
        at = self.active_timer
        if at.get("mode") == "countdown":
            from lazy_fit.db.models import set_setting
            set_setting("rest_timer_minimized", "0")
        self._nav_stack.append(
            (
                at["screen_widget"],
                at["screen_title"],
                at["minimize_fn"],
                at["show_back"],
                None,
            )
        )
        self._render_current()

    def cancel_active_timer(self) -> None:
        """Stop and discard any background timer (e.g. on language switch)."""
        if self.active_timer is None:
            return
        from lazy_fit.android_api import release_wake_lock

        self.active_timer["running"][0] = False
        release_wake_lock(self.active_timer["wake_lock_ref"][0])
        self.active_timer["wake_lock_ref"][0] = None
        self.active_timer = None

    def _render_current(self) -> None:
        """Render the top-of-stack screen inside the main window."""
        content, title, back_fn, show_back, _refresh_fn = self._nav_stack[-1]
        self.main_window.title = title

        children: list[toga.Widget] = []

        # Show timer banner at the very top when a timer is running but not on screen.
        at = self.active_timer
        if at is not None and content is not at["screen_widget"]:
            banner_btn = toga.Button(
                f"⏱ {at['banner_text']}",
                on_press=lambda w: self.restore_timer(),
                style=themed_pack(margin=4, width=120, background_color=COLOR_BTN_DANGER()),
            )
            at["banner_label"] = banner_btn
            banner_row = toga.Box(
                children=[banner_btn],
                style=Pack(direction=COLUMN, align_items="center"),
            )
            children.append(banner_row)

        can_go_back = len(self._nav_stack) > 1 and show_back
        if can_go_back:
            back_btn = toga.Button(
                f"‹ {t('back')}",
                on_press=lambda w: back_fn() if back_fn else self.nav_pop(),
                style=themed_pack(margin=4, background_color=COLOR_BTN_SECONDARY()),
            )
            nav_bar = toga.Box(
                children=[back_btn],
                style=Pack(direction=ROW, margin=4),
            )
            children.append(nav_bar)

        children.append(content)

        wrapper = toga.Box(
            children=children,
            style=Pack(direction=COLUMN, flex=1),
        )
        self.main_window.content = wrapper


def main() -> LazyFitApp:
    return LazyFitApp(
        "LazyFit",
        "com.lazyfit.lazy_fit",
    )

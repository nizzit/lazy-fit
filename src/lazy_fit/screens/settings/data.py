"""Data management settings screen — export and import."""

from __future__ import annotations

import json
import sys

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from lazy_fit.i18n import t


def build(app: toga.App) -> toga.Box:
    """Build and return the data management screen (export / import)."""

    async def on_export(widget: toga.Widget) -> None:
        from lazy_fit.db.models import export_all_data

        data = export_all_data()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        if sys.platform == "android":
            from lazy_fit.android_api import share_file

            shared_dir = app.paths.cache / "shared"
            shared_dir.mkdir(parents=True, exist_ok=True)
            tmp = shared_dir / "lazyfit_backup.json"
            tmp.write_text(json_str, encoding="utf-8")
            share_file(app, tmp)
        else:
            path = await app.main_window.dialog(
                toga.SaveFileDialog(
                    title=t("export_data"),
                    suggested_filename="lazyfit_backup.json",
                    file_types=["json"],
                )
            )
            if path is None:
                return
            path.write_text(json_str, encoding="utf-8")
            await app.main_window.dialog(
                toga.InfoDialog(t("export_data"), t("export_success"))
            )

    async def on_import(widget: toga.Widget) -> None:
        confirmed = await app.main_window.dialog(
            toga.ConfirmDialog(t("import_data"), t("import_confirm"))
        )
        if not confirmed:
            return

        if sys.platform == "android":
            from lazy_fit.android_api import pick_file, read_uri

            def on_file_picked(result_code: int, result_data: object) -> None:
                # RESULT_OK == -1 on Android
                if result_code != -1 or result_data is None:
                    return
                try:
                    uri = result_data.getData()  # type: ignore[union-attr]
                    text = read_uri(uri)
                    if text is None:
                        raise ValueError("read_uri returned None")
                    data = json.loads(text)
                    if not isinstance(data, dict) or "muscle_groups" not in data:
                        raise ValueError("missing required keys")
                except Exception:
                    app.add_background_task(  # type: ignore[union-attr]
                        lambda _: app.main_window.dialog(  # type: ignore[union-attr]
                            toga.ErrorDialog(t("import_data"), t("import_error"))
                        )
                    )
                    return

                from lazy_fit.db.models import import_all_data

                import_all_data(data)

                def _reload(_sender: object) -> None:
                    from lazy_fit.screens.home import build as build_home

                    app.nav_replace_root(build_home(app), t("app_name"))  # type: ignore[union-attr]
                    app.add_background_task(  # type: ignore[union-attr]
                        lambda _: app.main_window.dialog(  # type: ignore[union-attr]
                            toga.InfoDialog(t("import_data"), t("import_success"))
                        )
                    )

                app.add_background_task(_reload)  # type: ignore[union-attr]

            pick_file(app, on_complete=on_file_picked)
        else:
            path = await app.main_window.dialog(
                toga.OpenFileDialog(
                    title=t("import_data"),
                    file_types=["json"],
                )
            )
            if path is None:
                return
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or "muscle_groups" not in data:
                    raise ValueError("missing required keys")
            except Exception:
                await app.main_window.dialog(
                    toga.ErrorDialog(t("import_data"), t("import_error"))
                )
                return
            from lazy_fit.db.models import import_all_data

            import_all_data(data)
            from lazy_fit.screens.home import build as build_home

            app.nav_replace_root(build_home(app), t("app_name"))
            await app.main_window.dialog(
                toga.InfoDialog(t("import_data"), t("import_success"))
            )

    btn_style = Pack(margin=12, width=280)

    return toga.Box(
        children=[
            toga.Button(t("export_data"), on_press=on_export, style=btn_style),
            toga.Button(t("import_data"), on_press=on_import, style=btn_style),
        ],
        style=Pack(direction=COLUMN, align_items="center", margin=32),
    )

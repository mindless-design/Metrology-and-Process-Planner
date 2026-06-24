"""KLayout UI probe script builders."""

from __future__ import annotations

import textwrap


def main_window_snapshot_script() -> str:
    """Return a probe script that snapshots the live KLayout main window."""

    return textwrap.dedent(
        """
        import pya

        app = pya.Application.instance()
        main_window = app.main_window()
        report.update(
            {
                "app_type": type(app).__name__,
                "main_window_type": type(main_window).__name__,
                "has_menu": hasattr(main_window, "menu"),
                "has_current_view": hasattr(main_window, "current_view"),
            }
        )
        """
    )


def menu_registration_script() -> str:
    """Return a probe script that registers and snapshots plugin menu actions."""

    return textwrap.dedent(
        """
        import pya
        from metrology_process_planner.app.commands import DEFAULT_COMMANDS
        from metrology_process_planner.infrastructure.klayout.plugin import register_plugin

        app = pya.Application.instance()
        main_window = app.main_window()
        registration = register_plugin()
        menu = main_window.menu()
        menu_paths = {
            spec.command_id.value: registration.menu_path + "." + spec.menu_item_name
            for spec in DEFAULT_COMMANDS
        }
        report.update(
            {
                "app_type": type(app).__name__,
                "main_window_type": type(main_window).__name__,
                "menu_name": registration.menu_name,
                "menu_path": registration.menu_path,
                "command_count": registration.command_count,
                "menu_valid": bool(menu.is_valid(registration.menu_path)),
                "menu_paths": menu_paths,
                "menu_path_validity": {
                    key: bool(menu.is_valid(path)) for key, path in menu_paths.items()
                },
                "coverage_lanes": {
                    spec.command_id.value: spec.coverage_lane.value for spec in DEFAULT_COMMANDS
                },
            }
        )
        """
    )


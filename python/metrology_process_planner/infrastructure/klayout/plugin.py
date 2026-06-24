"""KLayout plugin registration boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.app.bootstrap import AppServices, build_app_services
from metrology_process_planner.app.commands import MENU_COMMANDS


class KLayoutRuntimeUnavailableError(RuntimeError):
    """Raised when KLayout-only behavior is used outside KLayout."""


@dataclass(frozen=True)
class PluginRegistration:
    """Summary of commands registered into the KLayout UI."""

    menu_name: str
    menu_path: str
    command_count: int


def import_pya() -> Any:
    """Import KLayout's runtime module or raise a clear adapter error."""

    try:
        import pya  # type: ignore[import-not-found]
    except ImportError as exc:
        raise KLayoutRuntimeUnavailableError(
            "KLayout module 'pya' is unavailable. Run this entrypoint from inside KLayout."
        ) from exc
    return pya


def register_plugin(
    pya_module: Optional[Any] = None,
    services: Optional[AppServices] = None,
) -> PluginRegistration:
    """Register the plugin with a live KLayout runtime.

    This function is intentionally small. Concrete UI controllers will be wired
    here once they exist, while domain and persistence behavior remains outside
    the KLayout boundary.
    """

    pya = pya_module if pya_module is not None else import_pya()
    app_services = services if services is not None else build_app_services()

    application = pya.Application.instance()
    main_window = application.main_window()
    menu = main_window.menu()

    menu_name = "metrology_process_planner"
    menu_path = MENU_COMMANDS[0].menu_path
    if not _menu_has_path(menu, menu_path):
        menu.insert_menu("tools_menu.end", menu_name, "Metrology Process Planner")

    for spec in MENU_COMMANDS:
        _register_action(
            pya,
            menu,
            menu_path,
            spec.menu_item_name,
            spec.title,
            lambda command_id=spec.command_id: app_services.command_router.route(command_id),
        )

    return PluginRegistration(
        menu_name=menu_name,
        menu_path=menu_path,
        command_count=len(MENU_COMMANDS),
    )


def _menu_has_path(menu: Any, menu_name: str) -> bool:
    try:
        return bool(menu.is_valid(menu_name))
    except AttributeError:
        return False


def _register_action(
    pya: Any,
    menu: Any,
    menu_path: str,
    action_name: str,
    title: str,
    callback: Any,
) -> None:
    action = pya.Action()
    action.title = title
    action.on_triggered(callback)
    menu.insert_item(f"{menu_path}.end", action_name, action)

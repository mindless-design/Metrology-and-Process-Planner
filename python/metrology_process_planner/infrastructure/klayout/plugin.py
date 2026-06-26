"""KLayout plugin registration boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.app.bootstrap import AppServices, build_app_services
from metrology_process_planner.app.commands import MENU_COMMANDS
from metrology_process_planner.app.layout_crop_repair import layout_crop_repair_service
from metrology_process_planner.app.mode_registry_config import load_configured_mode_registry
from metrology_process_planner.infrastructure.klayout.diagnostics_shell import (
    KLayoutDiagnosticsWidgetFactory,
)
from metrology_process_planner.infrastructure.klayout.layout_crop_exporter import (
    KLayoutLayoutCropExporter,
)
from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
from metrology_process_planner.infrastructure.klayout.recipe_path_adapter import (
    KLayoutRecipePathAdapter,
)
from metrology_process_planner.infrastructure.klayout.report_output_adapter import (
    KLayoutReportOutputAdapter,
)
from metrology_process_planner.infrastructure.klayout.session_editor_shell import (
    KLayoutSessionEditorWidgetFactory,
)
from metrology_process_planner.infrastructure.klayout.session_layout_adapter import (
    KLayoutSessionLayoutAdapter,
)
from metrology_process_planner.infrastructure.klayout.session_path_adapter import (
    KLayoutSessionPathAdapter,
)
from metrology_process_planner.infrastructure.klayout.setup_guide_shell import (
    KLayoutSetupGuideSurfaceFactory,
)
from metrology_process_planner.ui.diagnostics import DiagnosticsShell
from metrology_process_planner.ui.modeless import ModelessSurfaceShell
from metrology_process_planner.ui.session_editor import SessionEditorShell
from metrology_process_planner.workflows.overlays import CanvasOverlayManager


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
    app_services = services if services is not None else _build_klayout_services(pya)

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


def _build_klayout_services(pya: Any) -> AppServices:
    loaded_modes = load_configured_mode_registry()
    return build_app_services(
        path_adapter=KLayoutSessionPathAdapter(pya, loaded_modes.registry),
        recipe_path_adapter=KLayoutRecipePathAdapter(pya),
        layout_adapter=KLayoutSessionLayoutAdapter(pya),
        overlay_manager=CanvasOverlayManager(KLayoutOverlayBackend()),
        session_editor_shell=SessionEditorShell(KLayoutSessionEditorWidgetFactory(pya)),
        setup_guide_shell=ModelessSurfaceShell(KLayoutSetupGuideSurfaceFactory(pya)),
        diagnostics_shell=DiagnosticsShell(KLayoutDiagnosticsWidgetFactory(pya)),
        report_output_adapter=KLayoutReportOutputAdapter(pya),
        mode_registry=loaded_modes.registry,
        mode_load_warnings=loaded_modes.warnings,
        artifact_repair_service=layout_crop_repair_service(KLayoutLayoutCropExporter(pya)),
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

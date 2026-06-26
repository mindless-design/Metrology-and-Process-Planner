"""Pure application bootstrap helpers."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.app.bootstrap_commands import register_app_command_handlers
from metrology_process_planner.app.bootstrap_models import AppServices, UiControllers
from metrology_process_planner.app.bootstrap_ui import build_ui_controllers
from metrology_process_planner.app.capture_commands import (
    CaptureCommandService,
    active_capture_session,
    refresh_capture_session,
)
from metrology_process_planner.app.commands import CommandRegistry, build_default_registry
from metrology_process_planner.app.mode_registry_config import load_configured_mode_registry
from metrology_process_planner.app.recipe_commands import RecipeCommandService
from metrology_process_planner.app.recipe_path_adapter import RecipePathAdapter
from metrology_process_planner.app.recipe_session_attachment import refresh_editor_session
from metrology_process_planner.app.report_output_adapter import ReportOutputAdapter
from metrology_process_planner.app.session_layout_adapter import SessionLayoutAdapter
from metrology_process_planner.app.session_lifecycle import SessionLifecycleService
from metrology_process_planner.app.session_path_adapter import SessionPathAdapter
from metrology_process_planner.app.setup_commands import SetupGuideCommandService
from metrology_process_planner.diagnostics import (
    DiagnosticsService,
    InMemoryDiagnosticSink,
)
from metrology_process_planner.domains.session import ModeRegistry
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.drawing_store import SessionDrawingStore
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.ui.diagnostics import DiagnosticsShell
from metrology_process_planner.ui.modeless import ModelessSurfaceShell
from metrology_process_planner.ui.session_editor import SessionEditorShell
from metrology_process_planner.ui.shell import CommandRouter
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.canvas_interaction import CanvasInteractionEngine
from metrology_process_planner.workflows.overlays import CanvasOverlayManager
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService
from metrology_process_planner.workflows.selection import SelectionCoordinator

__all__ = ["AppServices", "UiControllers", "build_app_services"]


def build_app_services(
    path_adapter: SessionPathAdapter | None = None,
    recipe_path_adapter: RecipePathAdapter | None = None,
    layout_adapter: SessionLayoutAdapter | None = None,
    overlay_manager: CanvasOverlayManager | None = None,
    session_editor_shell: SessionEditorShell | None = None,
    setup_guide_shell: ModelessSurfaceShell | None = None,
    diagnostics_shell: DiagnosticsShell | None = None,
    report_output_adapter: ReportOutputAdapter | None = None,
    mode_registry: ModeRegistry | None = None,
    mode_load_warnings: tuple[str, ...] = (),
    artifact_repair_service: ArtifactRepairService | None = None,
) -> AppServices:
    """Create the default pure-Python service graph."""

    if mode_registry is None:
        loaded = load_configured_mode_registry()
        mode_registry = loaded.registry
        mode_load_warnings = mode_load_warnings + loaded.warnings
    graph = _build_service_graph(
        session_editor_shell,
        setup_guide_shell,
        diagnostics_shell,
        report_output_adapter,
        mode_registry,
        mode_load_warnings,
        recipe_path_adapter,
    )
    register_app_command_handlers(
        graph.command_registry,
        graph.ui,
        graph.session_lifecycle,
        graph.capture_commands,
        graph.setup_commands,
        graph.recipe_commands,
        (path_adapter, layout_adapter, overlay_manager, artifact_repair_service),
    )
    command_router = CommandRouter(graph.command_registry, graph.diagnostics_sink)
    graph.ui.setup_guide.set_command_router(command_router)
    graph.ui.session_editor.set_command_router(command_router)
    return _app_services(graph, command_router)


@dataclass(frozen=True)
class _ServiceGraph:
    command_registry: CommandRegistry
    diagnostics_sink: InMemoryDiagnosticSink
    diagnostics_service: DiagnosticsService
    mode_registry: ModeRegistry
    ui: UiControllers
    canvas_interaction: CanvasInteractionEngine
    capture_commands: CaptureCommandService
    setup_commands: SetupGuideCommandService
    recipe_commands: RecipeCommandService
    session_lifecycle: SessionLifecycleService


def _build_service_graph(
    session_editor_shell: SessionEditorShell | None,
    setup_guide_shell: ModelessSurfaceShell | None,
    diagnostics_shell: DiagnosticsShell | None,
    report_output_adapter: ReportOutputAdapter | None,
    mode_registry: ModeRegistry,
    mode_load_warnings: tuple[str, ...],
    recipe_path_adapter: RecipePathAdapter | None,
) -> _ServiceGraph:
    diagnostics_sink = InMemoryDiagnosticSink()
    diagnostics_service = DiagnosticsService(diagnostics_sink)
    ui = build_ui_controllers(
        diagnostics_sink,
        diagnostics_service,
        session_editor_shell,
        setup_guide_shell,
        diagnostics_shell,
        report_output_adapter,
        mode_registry,
        mode_load_warnings,
        recipe_path_adapter,
    )
    canvas_interaction = CanvasInteractionEngine(diagnostics_sink, mode_registry)
    capture_commands = _build_capture_commands(ui, canvas_interaction, mode_registry)
    return _ServiceGraph(
        build_default_registry(),
        diagnostics_sink,
        diagnostics_service,
        mode_registry,
        ui,
        canvas_interaction,
        capture_commands,
        SetupGuideCommandService(
            ui.setup_guide,
            canvas_interaction,
            session_updater=lambda session: refresh_editor_session(ui.session_editor, session),
            recipe_path_adapter=recipe_path_adapter,
            mode_registry=mode_registry,
        ),
        RecipeCommandService(ui.recipe_editor, recipe_path_adapter),
        _session_lifecycle(ui, capture_commands),
    )


def _app_services(graph: _ServiceGraph, command_router: CommandRouter) -> AppServices:
    return AppServices(
        commands=graph.command_registry,
        command_router=command_router,
        session_store=SessionJsonStore(graph.diagnostics_sink),
        capture_csv_exporter=CaptureCsvExporter(
            graph.diagnostics_sink,
            graph.mode_registry,
        ),
        drawing_store=SessionDrawingStore(),
        canvas_interaction=graph.canvas_interaction,
        capture_command_service=graph.capture_commands,
        session_lifecycle_service=graph.session_lifecycle,
        pending_capture_review=PendingCaptureReviewService(
            graph.diagnostics_sink,
            graph.mode_registry,
        ),
        overlay_manager_factory=CanvasOverlayManager,
        selection_coordinator_factory=lambda manager: SelectionCoordinator(
            manager,
            diagnostic_sink=graph.diagnostics_sink,
        ),
        session_editor_controller=graph.ui.session_editor,
        setup_guide_controller=graph.ui.setup_guide,
        recipe_editor_controller=graph.ui.recipe_editor,
        diagnostics_sink=graph.diagnostics_sink,
        diagnostics_service=graph.diagnostics_service,
        diagnostics_controller=graph.ui.diagnostics,
        reporting_workbench_controller=graph.ui.reporting_workbench,
        window_registry=graph.ui.window_registry,
    )


def _session_lifecycle(
    ui: UiControllers,
    capture_commands: CaptureCommandService,
) -> SessionLifecycleService:
    return SessionLifecycleService(
        ui.session_editor,
        ui.setup_guide,
        ui.diagnostics,
        capture_commands,
        ui.window_registry,
    )


def _build_capture_commands(
    ui: UiControllers,
    canvas_interaction: CanvasInteractionEngine,
    mode_registry: ModeRegistry,
) -> CaptureCommandService:
    return CaptureCommandService(
        canvas_interaction,
        session_provider=lambda: active_capture_session(ui.session_editor, ui.setup_guide),
        session_updater=lambda session: refresh_capture_session(
            ui.session_editor,
            ui.setup_guide,
            session,
        ),
        mode_registry=mode_registry,
    )

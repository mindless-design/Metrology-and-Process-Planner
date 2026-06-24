"""Pure application bootstrap helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import NamedTuple

from metrology_process_planner.app.commands import (
    CommandId,
    CommandRegistry,
    build_default_registry,
)
from metrology_process_planner.app.diagnostics import AdvancedDiagnosticsController
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.setup_commands import SetupGuideCommandService
from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.infrastructure.diagnostics import (
    DiagnosticsService,
    InMemoryDiagnosticSink,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.drawing_store import SessionDrawingStore
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.ui.shell import CommandRouter
from metrology_process_planner.workflows.canvas_interaction import CanvasInteractionEngine
from metrology_process_planner.workflows.overlays import CanvasOverlayBackend, CanvasOverlayManager
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService
from metrology_process_planner.workflows.selection import SelectionCoordinator


@dataclass(frozen=True)
class AppServices:
    """Container for services that do not require a live KLayout runtime."""

    commands: CommandRegistry
    command_router: CommandRouter
    session_store: SessionJsonStore
    capture_csv_exporter: CaptureCsvExporter
    drawing_store: SessionDrawingStore
    canvas_interaction: CanvasInteractionEngine
    pending_capture_review: PendingCaptureReviewService
    overlay_manager_factory: Callable[[CanvasOverlayBackend], CanvasOverlayManager]
    selection_coordinator_factory: Callable[[CanvasOverlayManager], SelectionCoordinator]
    session_editor_controller: SessionEditorController
    setup_guide_controller: SetupGuideController
    recipe_editor_controller: RecipeEditorController
    diagnostics_sink: InMemoryDiagnosticSink
    diagnostics_service: DiagnosticsService
    diagnostics_controller: AdvancedDiagnosticsController
    window_registry: WindowRegistry[object]


class UiControllers(NamedTuple):
    """Modeless UI controllers that share a single window registry."""

    diagnostics: AdvancedDiagnosticsController
    setup_guide: SetupGuideController
    recipe_editor: RecipeEditorController
    session_editor: SessionEditorController
    window_registry: WindowRegistry[object]


def build_app_services() -> AppServices:
    """Create the default pure-Python service graph."""

    command_registry = build_default_registry()
    diagnostics_sink = InMemoryDiagnosticSink()
    diagnostics_service = DiagnosticsService(diagnostics_sink)
    ui = _build_ui_controllers(diagnostics_sink, diagnostics_service)
    canvas_interaction = CanvasInteractionEngine(diagnostics_sink)
    setup_commands = SetupGuideCommandService(ui.setup_guide, canvas_interaction)
    _register_primary_command_handlers(command_registry, ui)
    _register_modeless_command_handlers(command_registry, ui)
    _register_setup_command_handlers(command_registry, setup_commands)
    command_router = CommandRouter(command_registry, diagnostics_sink)
    ui.setup_guide.set_command_router(command_router)
    return AppServices(
        commands=command_registry,
        command_router=command_router,
        session_store=SessionJsonStore(diagnostics_sink),
        capture_csv_exporter=CaptureCsvExporter(diagnostics_sink),
        drawing_store=SessionDrawingStore(),
        canvas_interaction=canvas_interaction,
        pending_capture_review=PendingCaptureReviewService(diagnostics_sink),
        overlay_manager_factory=CanvasOverlayManager,
        selection_coordinator_factory=lambda manager: SelectionCoordinator(
            manager,
            diagnostic_sink=diagnostics_sink,
        ),
        session_editor_controller=ui.session_editor,
        setup_guide_controller=ui.setup_guide,
        recipe_editor_controller=ui.recipe_editor,
        diagnostics_sink=diagnostics_sink,
        diagnostics_service=diagnostics_service,
        diagnostics_controller=ui.diagnostics,
        window_registry=ui.window_registry,
    )


def _register_primary_command_handlers(
    command_registry: CommandRegistry,
    ui: UiControllers,
) -> None:
    command_registry.register(
        CommandId.OPEN_SETUP_GUIDE,
        lambda: _open_setup_guide(ui.setup_guide),
    )
    command_registry.register(
        CommandId.OPEN_SESSION_EDITOR,
        lambda: _open_session_editor(ui.session_editor),
    )
    command_registry.register(
        CommandId.OPEN_RECIPE_EDITOR,
        lambda: _open_recipe_editor(ui.recipe_editor),
    )
    command_registry.register(CommandId.END_ACTIVE_SESSION, _end_active_session)
    command_registry.register(
        CommandId.OPEN_DIAGNOSTICS,
        lambda: _open_diagnostics(ui.diagnostics),
    )


def _register_setup_command_handlers(
    command_registry: CommandRegistry,
    setup_commands: SetupGuideCommandService,
) -> None:
    command_registry.register(
        CommandId.USE_GLOBAL_COORDINATES,
        setup_commands.use_global_coordinates,
    )
    command_registry.register(
        CommandId.USE_ORIGIN_COORDINATES,
        setup_commands.use_origin_coordinates,
    )
    command_registry.register(
        CommandId.START_ORIGIN_POINT_CAPTURE,
        setup_commands.start_origin_point_capture,
    )
    command_registry.register(
        CommandId.START_ORIGIN_REFERENCE_CAPTURE,
        setup_commands.start_origin_reference_capture,
    )
    command_registry.register(
        CommandId.START_ALIGNMENT_CAPTURE,
        setup_commands.start_alignment_capture,
    )
    command_registry.register(
        CommandId.START_SEM_ALIGNMENT_CAPTURE,
        setup_commands.start_sem_alignment_capture,
    )
    command_registry.register(CommandId.MARK_SETUP_COMPLETE, setup_commands.mark_setup_complete)


def _register_modeless_command_handlers(
    command_registry: CommandRegistry,
    ui: UiControllers,
) -> None:
    command_registry.register(
        CommandId.RETURN_TO_EDITOR,
        lambda: _open_session_editor(ui.session_editor),
    )
    command_registry.register(
        CommandId.CLOSE_SETUP_GUIDE,
        lambda: ui.setup_guide.close_current(),
    )


def _build_ui_controllers(
    diagnostics_sink: InMemoryDiagnosticSink,
    diagnostics_service: DiagnosticsService,
) -> UiControllers:
    window_registry: WindowRegistry[object] = WindowRegistry(diagnostic_sink=diagnostics_sink)
    session_editor = SessionEditorController(window_registry=window_registry)
    diagnostics = AdvancedDiagnosticsController(
        diagnostics_sink,
        diagnostics_service,
        window_registry=window_registry,
        editor_document_provider=lambda: session_editor.current_document,
    )
    return UiControllers(
        diagnostics=diagnostics,
        setup_guide=SetupGuideController(window_registry=window_registry),
        recipe_editor=RecipeEditorController(window_registry=window_registry),
        session_editor=session_editor,
        window_registry=window_registry,
    )


def _open_setup_guide(controller: SetupGuideController) -> None:
    controller.open_current()


def _open_session_editor(controller: SessionEditorController) -> None:
    controller.open_current_session()


def _open_recipe_editor(controller: RecipeEditorController) -> None:
    controller.open_current()


def _end_active_session() -> None:
    return None


def _open_diagnostics(controller: AdvancedDiagnosticsController) -> None:
    controller.open_current()

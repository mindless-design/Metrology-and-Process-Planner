"""Pure application bootstrap helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from metrology_process_planner.app.commands import (
    CommandId,
    CommandRegistry,
    build_default_registry,
)
from metrology_process_planner.app.diagnostics import AdvancedDiagnosticsController
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.setup_guide import SetupGuideController
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


def build_app_services() -> AppServices:
    """Create the default pure-Python service graph."""

    command_registry = build_default_registry()
    diagnostics_sink = InMemoryDiagnosticSink()
    diagnostics_service = DiagnosticsService(diagnostics_sink)
    diagnostics_controller = AdvancedDiagnosticsController(diagnostics_sink, diagnostics_service)
    setup_guide_controller = SetupGuideController()
    recipe_editor_controller = RecipeEditorController()
    session_editor_controller = SessionEditorController()
    command_registry.register(
        CommandId.START_OR_RESUME_SETUP,
        lambda: _open_setup_guide(setup_guide_controller),
    )
    command_registry.register(
        CommandId.OPEN_SESSION_EDITOR,
        lambda: _open_session_editor(session_editor_controller),
    )
    command_registry.register(
        CommandId.EDIT_RECIPE,
        lambda: _open_recipe_editor(recipe_editor_controller),
    )
    command_registry.register(CommandId.END_ACTIVE_SESSION, _end_active_session)
    command_registry.register(
        CommandId.OPEN_DIAGNOSTICS,
        lambda: _open_diagnostics(diagnostics_controller),
    )
    command_router = CommandRouter(command_registry, diagnostics_sink)
    return AppServices(
        commands=command_registry,
        command_router=command_router,
        session_store=SessionJsonStore(diagnostics_sink),
        capture_csv_exporter=CaptureCsvExporter(diagnostics_sink),
        drawing_store=SessionDrawingStore(),
        canvas_interaction=CanvasInteractionEngine(diagnostics_sink),
        pending_capture_review=PendingCaptureReviewService(diagnostics_sink),
        overlay_manager_factory=CanvasOverlayManager,
        selection_coordinator_factory=lambda manager: SelectionCoordinator(
            manager,
            diagnostic_sink=diagnostics_sink,
        ),
        session_editor_controller=session_editor_controller,
        setup_guide_controller=setup_guide_controller,
        recipe_editor_controller=recipe_editor_controller,
        diagnostics_sink=diagnostics_sink,
        diagnostics_service=diagnostics_service,
        diagnostics_controller=diagnostics_controller,
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

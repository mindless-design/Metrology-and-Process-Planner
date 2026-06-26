"""Application bootstrap container models."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import NamedTuple

from metrology_process_planner.app.capture_commands import CaptureCommandService
from metrology_process_planner.app.commands import CommandRegistry
from metrology_process_planner.app.diagnostics import AdvancedDiagnosticsController
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.app.reporting_workbench import ReportingWorkbenchController
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_lifecycle import SessionLifecycleService
from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.diagnostics import (
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
    capture_command_service: CaptureCommandService
    session_lifecycle_service: SessionLifecycleService
    pending_capture_review: PendingCaptureReviewService
    overlay_manager_factory: Callable[[CanvasOverlayBackend], CanvasOverlayManager]
    selection_coordinator_factory: Callable[[CanvasOverlayManager], SelectionCoordinator]
    session_editor_controller: SessionEditorController
    setup_guide_controller: SetupGuideController
    recipe_editor_controller: RecipeEditorController
    diagnostics_sink: InMemoryDiagnosticSink
    diagnostics_service: DiagnosticsService
    diagnostics_controller: AdvancedDiagnosticsController
    reporting_workbench_controller: ReportingWorkbenchController
    window_registry: WindowRegistry[object]


class UiControllers(NamedTuple):
    """Modeless UI controllers that share a single window registry."""

    diagnostics: AdvancedDiagnosticsController
    setup_guide: SetupGuideController
    recipe_editor: RecipeEditorController
    session_editor: SessionEditorController
    reporting_workbench: ReportingWorkbenchController
    window_registry: WindowRegistry[object]

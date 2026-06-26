"""UI controller construction for application bootstrap."""

from __future__ import annotations

from metrology_process_planner.app.bootstrap_models import UiControllers
from metrology_process_planner.app.diagnostics import AdvancedDiagnosticsController
from metrology_process_planner.app.recipe_editor import RecipeEditorController
from metrology_process_planner.app.recipe_path_adapter import RecipePathAdapter
from metrology_process_planner.app.recipe_session_attachment import (
    active_session_from_editor,
    refresh_editor_session,
)
from metrology_process_planner.app.report_output_adapter import ReportOutputAdapter
from metrology_process_planner.app.reporting_artifact_repair import (
    ReportingWorkbenchArtifactRepairService,
)
from metrology_process_planner.app.reporting_workbench import ReportingWorkbenchController
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.diagnostics import (
    DiagnosticsService,
    InMemoryDiagnosticSink,
)
from metrology_process_planner.domains.session import ModeRegistry
from metrology_process_planner.ui.diagnostics import DiagnosticsShell
from metrology_process_planner.ui.modeless import ModelessSurfaceShell
from metrology_process_planner.ui.session_editor import SessionEditorShell
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter


def build_ui_controllers(
    diagnostics_sink: InMemoryDiagnosticSink,
    diagnostics_service: DiagnosticsService,
    session_editor_shell: SessionEditorShell | None = None,
    setup_guide_shell: ModelessSurfaceShell | None = None,
    diagnostics_shell: DiagnosticsShell | None = None,
    report_output_adapter: ReportOutputAdapter | None = None,
    mode_registry: ModeRegistry | None = None,
    mode_load_warnings: tuple[str, ...] = (),
    recipe_path_adapter: RecipePathAdapter | None = None,
) -> UiControllers:
    """Build modeless UI controllers around one shared window registry."""

    window_registry: WindowRegistry[object] = WindowRegistry(diagnostic_sink=diagnostics_sink)
    session_editor = SessionEditorController(
        shell=session_editor_shell,
        mode_registry=mode_registry,
        window_registry=window_registry,
    )
    diagnostics = AdvancedDiagnosticsController(
        diagnostics_sink,
        diagnostics_service,
        shell=diagnostics_shell,
        mode_registry=mode_registry,
        mode_load_warnings=mode_load_warnings,
        window_registry=window_registry,
        editor_document_provider=lambda: session_editor.current_document,
    )
    return UiControllers(
        diagnostics=diagnostics,
        setup_guide=_setup_guide_controller(window_registry, setup_guide_shell, mode_registry),
        recipe_editor=_recipe_editor_controller(
            window_registry,
            session_editor,
            recipe_path_adapter,
            mode_registry,
        ),
        session_editor=session_editor,
        reporting_workbench=_reporting_controller(
            window_registry,
            session_editor,
            report_output_adapter,
            mode_registry,
        ),
        window_registry=window_registry,
    )


def _setup_guide_controller(
    window_registry: WindowRegistry[object],
    setup_guide_shell: ModelessSurfaceShell | None,
    mode_registry: ModeRegistry | None,
) -> SetupGuideController:
    return SetupGuideController(
        presenter=SetupGuidePresenter(mode_registry=mode_registry),
        shell=setup_guide_shell,
        window_registry=window_registry,
    )


def _recipe_editor_controller(
    window_registry: WindowRegistry[object],
    session_editor: SessionEditorController,
    recipe_path_adapter: RecipePathAdapter | None,
    mode_registry: ModeRegistry | None,
) -> RecipeEditorController:
    return RecipeEditorController(
        window_registry=window_registry,
        active_session_provider=lambda: active_session_from_editor(session_editor),
        active_session_updater=lambda session: refresh_editor_session(session_editor, session),
        recipe_path_adapter=recipe_path_adapter,
        mode_registry=mode_registry,
    )


def _reporting_controller(
    window_registry: WindowRegistry[object],
    session_editor: SessionEditorController,
    report_output_adapter: ReportOutputAdapter | None,
    mode_registry: ModeRegistry | None,
) -> ReportingWorkbenchController:
    return ReportingWorkbenchController(
        window_registry=window_registry,
        artifact_repair_service=ReportingWorkbenchArtifactRepairService(
            mode_registry=mode_registry,
        ),
        output_adapter=report_output_adapter,
        active_session_updater=lambda session: refresh_editor_session(session_editor, session),
        mode_registry=mode_registry,
    )

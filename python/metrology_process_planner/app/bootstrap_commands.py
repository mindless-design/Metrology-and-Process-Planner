"""Command registration helpers for app bootstrap."""

from __future__ import annotations

from metrology_process_planner.app import session_editor_commands
from metrology_process_planner.app.bootstrap_models import UiControllers
from metrology_process_planner.app.capture_commands import (
    CaptureCommandService,
    register_capture_command_handlers,
)
from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.recipe_commands import (
    RecipeCommandService,
    register_recipe_command_handlers,
)
from metrology_process_planner.app.recipe_session_attachment import active_session_from_editor
from metrology_process_planner.app.return_to_editor import open_session_editor, return_to_editor
from metrology_process_planner.app.session_editor_command_dispatch import dispatch_editor_action
from metrology_process_planner.app.session_layout_adapter import SessionLayoutAdapter
from metrology_process_planner.app.session_lifecycle import SessionLifecycleService
from metrology_process_planner.app.session_path_adapter import SessionPathAdapter
from metrology_process_planner.app.setup_commands import (
    SetupGuideCommandService,
    register_setup_command_handlers,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.editor.view_models import EditorActionType
from metrology_process_planner.workflows.overlays import CanvasOverlayManager


def register_app_command_handlers(
    command_registry: CommandRegistry,
    ui: UiControllers,
    session_lifecycle: SessionLifecycleService,
    capture_commands: CaptureCommandService,
    setup_commands: SetupGuideCommandService,
    recipe_commands: RecipeCommandService,
    adapters: tuple[
        SessionPathAdapter | None,
        SessionLayoutAdapter | None,
        CanvasOverlayManager | None,
        ArtifactRepairService | None,
    ],
) -> None:
    """Register app, capture, editor, and setup command handlers."""

    _register_primary_command_handlers(command_registry, ui, session_lifecycle)
    _register_modeless_command_handlers(command_registry, ui)
    register_capture_command_handlers(command_registry, capture_commands)
    register_recipe_command_handlers(command_registry, recipe_commands)
    path_adapter, layout_adapter, overlay_manager, artifact_repair_service = adapters
    session_editor_commands.register_session_editor_command_handlers(
        command_registry,
        ui.session_editor,
        path_adapter,
        layout_adapter,
        overlay_manager,
        artifact_repair_service,
    )
    register_setup_command_handlers(command_registry, setup_commands)
    command_registry.register(
        CommandId.ATTACH_RECIPE,
        lambda: _attach_recipe_from_active_surface(ui, setup_commands),
    )


def _register_primary_command_handlers(
    command_registry: CommandRegistry,
    ui: UiControllers,
    session_lifecycle: SessionLifecycleService,
) -> None:
    command_registry.register(CommandId.OPEN_SETUP_GUIDE, lambda: _open_setup_guide(ui))
    command_registry.register(
        CommandId.OPEN_SESSION_EDITOR,
        lambda: open_session_editor(ui.session_editor),
    )
    command_registry.register(
        CommandId.OPEN_RECIPE_EDITOR,
        lambda: ui.recipe_editor.open_current(),
    )
    command_registry.register(CommandId.END_ACTIVE_SESSION, session_lifecycle.end_active_session)
    command_registry.register(CommandId.OPEN_DIAGNOSTICS, lambda: ui.diagnostics.open_current())
    command_registry.register(
        CommandId.OPEN_REPORTING_WORKBENCH,
        lambda: _open_reporting_workbench(ui),
    )


def _register_modeless_command_handlers(
    command_registry: CommandRegistry,
    ui: UiControllers,
) -> None:
    command_registry.register(CommandId.RETURN_TO_EDITOR, lambda: return_to_editor(ui))
    command_registry.register(
        CommandId.CLOSE_SETUP_GUIDE,
        lambda: ui.setup_guide.close_current(),
    )


def _open_setup_guide(ui: UiControllers) -> None:
    session = active_session_from_editor(ui.session_editor)
    if session is not None:
        ui.setup_guide.set_active_session(session)
    ui.setup_guide.open_current()


def _open_reporting_workbench(ui: UiControllers) -> object:
    document = ui.session_editor.current_document
    paths = ui.session_editor.current_paths
    if document is None or paths is None:
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "unavailable",
            "No active session editor document is available.",
        )
    return ui.reporting_workbench.open_document(document, paths)


def _attach_recipe_from_active_surface(
    ui: UiControllers,
    setup_commands: SetupGuideCommandService,
) -> CommandRouteResult:
    routed = ui.session_editor.routed_action
    if routed is not None and routed.action_type is EditorActionType.ATTACH_RECIPE:
        return dispatch_editor_action(ui.session_editor, CommandId.ATTACH_RECIPE, routed)
    return setup_commands.attach_recipe()

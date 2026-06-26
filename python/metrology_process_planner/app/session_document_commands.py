"""App command registration for explicit session document lifecycle actions."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandHandler, CommandId, CommandRegistry
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_layout_adapter import SessionLayoutAdapter
from metrology_process_planner.app.session_layout_command_service import (
    SessionLayoutCommandService,
)
from metrology_process_planner.app.session_lifecycle_command_service import (
    SessionLifecycleCommandService,
)
from metrology_process_planner.app.session_path_adapter import SessionPathAdapter
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.overlays import CanvasOverlayManager


def register_document_lifecycle_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
    path_adapter: SessionPathAdapter | None = None,
    layout_adapter: SessionLayoutAdapter | None = None,
    overlay_manager: CanvasOverlayManager | None = None,
) -> None:
    """Register explicit session document lifecycle command handlers."""

    lifecycle = SessionLifecycleCommandService(controller, path_adapter)
    layout = SessionLayoutCommandService(controller, layout_adapter, overlay_manager)
    registry.register(CommandId.OPEN_SESSION, lifecycle.open_session)
    registry.register(CommandId.NEW_SESSION, lifecycle.new_session)
    registry.register(CommandId.OPEN_RECENT_SESSION, lifecycle.open_recent_session)
    registry.register(CommandId.SAVE_SESSION, lifecycle.save_session)
    registry.register(CommandId.SAVE_SESSION_AS, lifecycle.save_session_as)
    registry.register(CommandId.CLOSE_SESSION, lifecycle.close_session)
    registry.register(CommandId.REVEAL_SESSION_FOLDER, lifecycle.reveal_session_folder)
    registry.register(CommandId.VALIDATE_SESSION, lifecycle.validate_session)
    registry.register(CommandId.REPAIR_SESSION, _unavailable(CommandId.REPAIR_SESSION))
    registry.register(
        CommandId.IMPORT_LEGACY_SESSION_FOLDER,
        _unavailable(CommandId.IMPORT_LEGACY_SESSION_FOLDER),
    )
    registry.register(
        CommandId.BIND_CURRENT_LAYOUT_TO_SESSION,
        layout.bind_current_layout_to_session,
    )


def _unavailable(command_id: CommandId) -> CommandHandler:
    return lambda: _unavailable_result(command_id)


def _unavailable_result(command_id: CommandId) -> CommandRouteResult:
    return CommandRouteResult(
        command_id,
        "unavailable",
        f"{command_id.value} requires a user-selected path or layout binding.",
        next_ui_hint="Open the Session Editor start screen and choose the command there.",
    )

"""Command handlers that delegate session editor actions through the app router."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.session_document_commands import (
    register_document_lifecycle_command_handlers,
)
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_capture_commands import (
    SessionEditorCaptureCommandMixin,
)
from metrology_process_planner.app.session_editor_command_dispatch import (
    dispatch_editor_action,
)
from metrology_process_planner.app.session_editor_command_results import (
    action_label,
    command_result,
    no_document,
)
from metrology_process_planner.app.session_layout_adapter import SessionLayoutAdapter
from metrology_process_planner.app.session_path_adapter import SessionPathAdapter
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.editing import mark_clean
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType
from metrology_process_planner.workflows.overlays import CanvasOverlayManager


class SessionEditorCommandService(SessionEditorCaptureCommandMixin):
    """Translate app-level session commands into editor workflow actions."""

    def __init__(self, controller: SessionEditorController) -> None:
        self._controller = controller

    def save_session_edits(self) -> CommandRouteResult:
        """Save the active editor document through the editor dispatcher."""

        return dispatch_editor_action(
            self._controller,
            CommandId.SAVE_SESSION_EDITS,
            EditorAction(EditorActionType.SAVE_EDITS, action_label(EditorActionType.SAVE_EDITS)),
        )

    def discard_unsaved_edits(self) -> CommandRouteResult:
        """Discard in-memory editor edits without touching canonical session files."""

        document = self._controller.current_document
        if document is None:
            return no_document(CommandId.DISCARD_UNSAVED_EDITS, "discarding edits")
        clean = mark_clean(document, document.dirty_state.last_saved_revision)
        self._controller.replace_current_document(clean)
        return command_result(
            CommandId.DISCARD_UNSAVED_EDITS,
            EditorActionResult("success", clean, "Discarded unsaved editor edits."),
        )

def register_session_editor_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
    path_adapter: SessionPathAdapter | None = None,
    layout_adapter: SessionLayoutAdapter | None = None,
    overlay_manager: CanvasOverlayManager | None = None,
    artifact_repair_service: ArtifactRepairService | None = None,
) -> None:
    """Register command handlers owned by the unified session editor."""

    service = SessionEditorCommandService(controller)
    register_document_lifecycle_command_handlers(
        registry,
        controller,
        path_adapter,
        layout_adapter,
        overlay_manager,
    )
    _register_editor_action_commands(registry, service)
    _register_related_editor_command_groups(registry, controller, artifact_repair_service)


def _register_editor_action_commands(
    registry: CommandRegistry,
    service: SessionEditorCommandService,
) -> None:
    registry.register(CommandId.SAVE_SESSION_EDITS, service.save_session_edits)
    registry.register(CommandId.DISCARD_UNSAVED_EDITS, service.discard_unsaved_edits)
    registry.register(CommandId.SAVE_PENDING_CAPTURE, service.save_pending_capture)
    registry.register(CommandId.SAVE_COMPOSITE_CAPTURE, service.save_composite_capture)
    registry.register(CommandId.RETAKE_PENDING_CAPTURE, service.retake_pending_capture)
    registry.register(CommandId.RETAKE_PARENT_CAPTURE, service.retake_parent_capture)
    registry.register(CommandId.RETAKE_INNER_FEATURE, service.retake_inner_feature)
    registry.register(CommandId.DISCARD_PENDING_CAPTURE, service.discard_pending_capture)
    registry.register(CommandId.ADD_MEASUREMENT, service.add_measurement)
    registry.register(CommandId.SAVE_MEASUREMENT, service.save_measurement)
    registry.register(CommandId.RETAKE_MEASUREMENT_LINE, service.retake_measurement_line)
    registry.register(CommandId.DISCARD_MEASUREMENT, service.discard_measurement)


def _register_related_editor_command_groups(
    registry: CommandRegistry,
    controller: SessionEditorController,
    artifact_repair_service: ArtifactRepairService | None,
) -> None:
    from metrology_process_planner.app.session_editor_artifact_commands import (
        register_artifact_command_handlers,
    )
    from metrology_process_planner.app.session_editor_completion_commands import (
        register_completion_command_handlers,
    )
    from metrology_process_planner.app.session_editor_export_commands import (
        register_export_command_handlers,
    )
    from metrology_process_planner.app.session_editor_process_commands import (
        register_process_editor_command_handlers,
    )

    register_artifact_command_handlers(registry, controller, artifact_repair_service)
    register_completion_command_handlers(registry, controller)
    register_export_command_handlers(registry, controller)
    register_process_editor_command_handlers(registry, controller)

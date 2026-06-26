"""Map editor actions to app-level command IDs."""

from __future__ import annotations

from typing import Optional

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


def command_for_action(action: EditorAction) -> Optional[CommandId]:
    """Return the app command for an editor action when one exists."""

    return _EDITOR_COMMANDS.get(action.action_type)


_EDITOR_COMMANDS: dict[EditorActionType, CommandId] = {
    EditorActionType.ADD_CAPTURE: CommandId.START_CAPTURE,
    EditorActionType.CANCEL_CAPTURE: CommandId.CANCEL_CAPTURE,
    EditorActionType.ADD_MEASUREMENT: CommandId.ADD_MEASUREMENT,
    EditorActionType.ATTACH_RECIPE: CommandId.ATTACH_RECIPE,
    EditorActionType.COMPOSITE_DISCARD: CommandId.DISCARD_PENDING_CAPTURE,
    EditorActionType.COMPOSITE_RETAKE_INNER: CommandId.RETAKE_INNER_FEATURE,
    EditorActionType.COMPOSITE_RETAKE_PARENT: CommandId.RETAKE_PARENT_CAPTURE,
    EditorActionType.COMPOSITE_SAVE: CommandId.SAVE_COMPOSITE_CAPTURE,
    EditorActionType.DETACH_RECIPE: CommandId.DETACH_RECIPE,
    EditorActionType.DISCARD_MEASUREMENT: CommandId.DISCARD_MEASUREMENT,
    EditorActionType.EXIT_SESSION: CommandId.END_ACTIVE_SESSION,
    EditorActionType.EXPORT_CSV: CommandId.EXPORT_CSV,
    EditorActionType.BUILD_POWERPOINT: CommandId.OPEN_REPORTING_WORKBENCH,
    EditorActionType.OPEN_OUTPUT_FOLDER: CommandId.OPEN_OUTPUT_FOLDER,
    EditorActionType.PENDING_DISCARD: CommandId.DISCARD_PENDING_CAPTURE,
    EditorActionType.PENDING_RETAKE: CommandId.RETAKE_PENDING_CAPTURE,
    EditorActionType.PENDING_SAVE: CommandId.SAVE_PENDING_CAPTURE,
    EditorActionType.REGENERATE_ARTIFACT: CommandId.REGENERATE_ARTIFACT,
    EditorActionType.SCAN_ARTIFACTS: CommandId.SCAN_ARTIFACTS,
    EditorActionType.REGENERATE_MISSING_ARTIFACTS: CommandId.REGENERATE_MISSING_ARTIFACTS,
    EditorActionType.REGENERATE_STALE_ARTIFACTS: CommandId.REGENERATE_STALE_ARTIFACTS,
    EditorActionType.RELINK_ARTIFACT: CommandId.RELINK_ARTIFACT,
    EditorActionType.EXPORT_ARTIFACT_MANIFEST: CommandId.EXPORT_ARTIFACT_MANIFEST,
    EditorActionType.REGENERATE_PROCESS_OUTPUT: CommandId.REGENERATE_PROCESS_OUTPUT,
    EditorActionType.REOPEN_SETUP: CommandId.OPEN_SETUP_GUIDE,
    EditorActionType.TAKE_ANOTHER_MEASUREMENT: CommandId.TAKE_ANOTHER_MEASUREMENT,
    EditorActionType.RETURN_TO_EDITOR: CommandId.RETURN_TO_EDITOR,
    EditorActionType.DONE: CommandId.DONE,
    EditorActionType.RETAKE_MEASUREMENT_LINE: CommandId.RETAKE_MEASUREMENT_LINE,
    EditorActionType.SAVE_EDITS: CommandId.SAVE_SESSION_EDITS,
    EditorActionType.SAVE_MEASUREMENT: CommandId.SAVE_MEASUREMENT,
    EditorActionType.VALIDATE_PROCESS_CONTEXT: CommandId.VALIDATE_PROCESS_CONTEXT,
}

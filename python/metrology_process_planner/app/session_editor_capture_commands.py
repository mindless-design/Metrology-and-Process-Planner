"""Capture and measurement command methods for the session editor service."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_editor_command_dispatch import (
    dispatch_selected_editor_action,
)
from metrology_process_planner.app.session_editor_command_results import (
    selected_pending_is_composite,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.view_models import EditorActionType


class SessionEditorCaptureCommandMixin:
    """Route capture and measurement commands through selected editor items."""

    def save_pending_capture(self: Any) -> CommandRouteResult:
        """Save the selected pending capture through the editor workflow."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.SAVE_PENDING_CAPTURE,
            EditorActionType.PENDING_SAVE,
        )

    def retake_pending_capture(self: Any) -> CommandRouteResult:
        """Retake the selected pending capture through the editor workflow."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.RETAKE_PENDING_CAPTURE,
            EditorActionType.PENDING_RETAKE,
        )

    def discard_pending_capture(self: Any) -> CommandRouteResult:
        """Discard the selected pending capture through the editor workflow."""

        action_type = EditorActionType.PENDING_DISCARD
        document = self._controller.current_document
        if document is not None and selected_pending_is_composite(document):
            action_type = EditorActionType.COMPOSITE_DISCARD
        return dispatch_selected_editor_action(
            self._controller,
            CommandId.DISCARD_PENDING_CAPTURE,
            action_type,
        )

    def save_composite_capture(self: Any) -> CommandRouteResult:
        """Save the selected pending composite through the editor workflow."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.SAVE_COMPOSITE_CAPTURE,
            EditorActionType.COMPOSITE_SAVE,
        )

    def retake_parent_capture(self: Any) -> CommandRouteResult:
        """Retake the selected composite parent site through the editor workflow."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.RETAKE_PARENT_CAPTURE,
            EditorActionType.COMPOSITE_RETAKE_PARENT,
        )

    def retake_inner_feature(self: Any) -> CommandRouteResult:
        """Retake the selected composite child feature through the editor workflow."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.RETAKE_INNER_FEATURE,
            EditorActionType.COMPOSITE_RETAKE_INNER,
        )

    def add_measurement(self: Any) -> CommandRouteResult:
        """Arm measurement capture for the selected saved capture."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.ADD_MEASUREMENT,
            EditorActionType.ADD_MEASUREMENT,
        )

    def save_measurement(self: Any) -> CommandRouteResult:
        """Save pending measurement edits through the editor workflow."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.SAVE_MEASUREMENT,
            EditorActionType.SAVE_MEASUREMENT,
        )

    def retake_measurement_line(self: Any) -> CommandRouteResult:
        """Retake the selected pending measurement line."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.RETAKE_MEASUREMENT_LINE,
            EditorActionType.RETAKE_MEASUREMENT_LINE,
        )

    def discard_measurement(self: Any) -> CommandRouteResult:
        """Discard the selected pending measurement."""

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.DISCARD_MEASUREMENT,
            EditorActionType.DISCARD_MEASUREMENT,
        )

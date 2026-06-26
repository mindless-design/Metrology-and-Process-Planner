"""Session document lifecycle command service."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_document_command_results import (
    open_result,
    selection_result,
)
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_command_results import no_document
from metrology_process_planner.app.session_path_adapter import (
    PathSelection,
    SessionPathAdapter,
    UnavailableSessionPathAdapter,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor.warning_visibility import editor_visible_warnings


class SessionLifecycleCommandService:
    """Translate path-oriented document commands into controller calls."""

    def __init__(
        self,
        controller: SessionEditorController,
        path_adapter: SessionPathAdapter | None = None,
    ) -> None:
        self._controller = controller
        self._path_adapter = (
            path_adapter if path_adapter is not None else UnavailableSessionPathAdapter()
        )

    def new_session(self) -> CommandRouteResult:
        """Create a session from operator-selected folder, label, and mode."""

        selection = self._path_adapter.select_new_session()
        if selection.status != "selected":
            return selection_result(CommandId.NEW_SESSION, selection.status, selection.message)
        result = self._controller.new_session(selection.to_request())
        return open_result(CommandId.NEW_SESSION, result)

    def open_session(self) -> CommandRouteResult:
        """Open an operator-selected session JSON file or session folder."""

        selection = self._path_adapter.select_open_session()
        return self._open_selected_path(CommandId.OPEN_SESSION, selection)

    def open_recent_session(self) -> CommandRouteResult:
        """Open an operator-selected recent session path."""

        recent_paths = self._controller.recent_session_paths()
        selection = self._path_adapter.select_recent_session(recent_paths)
        return self._open_selected_path(CommandId.OPEN_RECENT_SESSION, selection)

    def save_session(self) -> CommandRouteResult:
        """Save the active document through explicit lifecycle save."""

        return open_result(CommandId.SAVE_SESSION, self._controller.save_current_session())

    def save_session_as(self) -> CommandRouteResult:
        """Save to an operator-selected session folder or session JSON path."""

        selection = self._path_adapter.select_save_as_destination()
        if selection.status != "selected" or selection.path is None:
            return selection_result(
                CommandId.SAVE_SESSION_AS,
                selection.status,
                selection.message,
            )
        return open_result(
            CommandId.SAVE_SESSION_AS,
            self._controller.save_current_session_as(selection.path),
        )

    def close_session(self) -> CommandRouteResult:
        """Close the active document, blocking if dirty until the UI supplies a choice."""

        return open_result(CommandId.CLOSE_SESSION, self._controller.close_current_session())

    def reveal_session_folder(self) -> CommandRouteResult:
        """Resolve the active session folder for platform-specific reveal UI."""

        paths = self._controller.current_paths
        if paths is None:
            return no_document(CommandId.REVEAL_SESSION_FOLDER, "revealing the session folder")
        return CommandRouteResult(
            CommandId.REVEAL_SESSION_FOLDER,
            "success",
            "Session folder path resolved.",
            output_path=str(paths.folder),
        )

    def validate_session(self) -> CommandRouteResult:
        """Report validation status for the active document."""

        document = self._controller.current_document
        if document is None:
            return no_document(CommandId.VALIDATE_SESSION, "validation")
        warning_ids = tuple(warning.id for warning in editor_visible_warnings(document.session))
        return CommandRouteResult(
            CommandId.VALIDATE_SESSION,
            "warning" if warning_ids else "success",
            "Session has warnings." if warning_ids else "Session document is valid.",
            updated_document_id=document.session.id,
            selected_item_id=document.selection.selected_item_id,
            warning_ids=warning_ids,
        )

    def _open_selected_path(
        self,
        command_id: CommandId,
        selection: PathSelection,
    ) -> CommandRouteResult:
        if selection.status != "selected" or selection.path is None:
            return selection_result(command_id, selection.status, selection.message)
        return open_result(command_id, self._controller.open_session_path(selection.path))

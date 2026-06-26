"""Action routing methods for the session editor controller."""

from __future__ import annotations

from typing import Any, Optional, cast

from metrology_process_planner.app.active_session import ActiveSessionContext
from metrology_process_planner.app.session_editor_command_map import command_for_action
from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction


class SessionEditorRoutingMixin:
    """Route editor actions through app commands or the workflow dispatcher."""

    current_document: Optional[SessionDocument]
    last_action_result: Optional[EditorActionResult]
    _routed_action: Optional[EditorAction]

    def dispatch_current_action(
        self: Any,
        action: EditorAction,
        *,
        allow_app_route: bool = True,
    ) -> Optional[EditorActionResult]:
        """Dispatch an editor action against the active document and rerender."""

        if self.current_document is None:
            return None
        if allow_app_route and self._route_app_command(action):
            routed_result = cast(Optional[EditorActionResult], self.last_action_result)
            return routed_result
        dispatcher = self._dispatcher
        if dispatcher is None:
            dispatcher = EditorActionDispatcher(mode_registry=self._mode_registry)
        result = cast(EditorActionResult, dispatcher.dispatch(self.current_document, action))
        self.current_document = result.document
        self.active_context = ActiveSessionContext.from_document(result.document)
        self.last_action_result = result
        self._render_current()
        return result

    def replace_current_document(self: Any, document: SessionDocument) -> None:
        """Replace the active document after an app-owned command update."""

        self.current_document = document
        self.active_context = ActiveSessionContext.from_document(document)
        self._render_current()

    @property
    def routed_action(self: Any) -> Optional[EditorAction]:
        """Return the editor action currently being routed through app commands."""

        return cast(Optional[EditorAction], self._routed_action)

    def _route_app_command(self: Any, action: EditorAction) -> bool:
        command_id = command_for_action(action)
        if command_id is None or self._command_router is None:
            return False
        self._routed_action = action
        try:
            self.last_command_result = self._command_router.route(command_id)
        finally:
            self._routed_action = None
        if self.current_document is None:
            return True
        self._render_current()
        return True

"""Session-editor callbacks used by recipe attachment commands."""

from __future__ import annotations

from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder


def active_session_from_editor(controller: SessionEditorController) -> SessionRecord | None:
    """Return the canonical session currently shown in the editor."""

    if controller.current_document is None:
        return None
    return controller.current_document.session


def refresh_editor_session(controller: SessionEditorController, session: SessionRecord) -> None:
    """Rebuild and refresh the editor document after session-level updates."""

    raw_payload = {}
    if controller.current_document is not None:
        raw_payload = dict(controller.current_document.raw_payload)
    controller.open_document(SessionDocumentBuilder().build(session, raw_payload))

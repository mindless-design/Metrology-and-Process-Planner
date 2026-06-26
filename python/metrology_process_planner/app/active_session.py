"""Single active session context for document-backed workflows."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

from metrology_process_planner.domains.session import SourceLayoutContext, WorkflowState
from metrology_process_planner.workflows.editor.document import SessionDocument


@dataclass(frozen=True)
class ActiveSessionContext:
    """Track the one editable Process Planner session document in use."""

    active_session_id: str = ""
    active_session_path: Optional[Path] = None
    active_document: Optional[SessionDocument] = None
    source_layout_binding: SourceLayoutContext = SourceLayoutContext()
    dirty_state: bool = False
    last_saved_revision: int = 0
    workflow_state: WorkflowState = WorkflowState()
    selected_item_id: str = ""

    @classmethod
    def from_document(cls, document: SessionDocument) -> ActiveSessionContext:
        """Build active context metadata from a loaded editor document."""

        return cls(
            active_session_id=document.session.id,
            active_session_path=document.loaded_path,
            active_document=document,
            source_layout_binding=document.session.source_layout,
            dirty_state=document.dirty_state.is_dirty,
            last_saved_revision=document.dirty_state.last_saved_revision,
            workflow_state=document.session.workflow,
            selected_item_id=document.selection.selected_item_id,
        )

    def with_document(self, document: Optional[SessionDocument]) -> ActiveSessionContext:
        """Return updated active context for a document or cleared session."""

        if document is None:
            return ActiveSessionContext()
        return ActiveSessionContext.from_document(document)

    def mark_closed(self) -> ActiveSessionContext:
        """Return a cleared context after session close."""

        return replace(self, active_document=None, active_session_id="", active_session_path=None)

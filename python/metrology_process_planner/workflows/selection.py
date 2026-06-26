"""Selection synchronization between editor state and canvas overlays."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.canvas_interaction import CanvasInteractionEngine
from metrology_process_planner.workflows.canvas_state import find_canvas_object
from metrology_process_planner.workflows.overlays import CanvasOverlayManager


class EditorSelectionSink(Protocol):
    """Future editor callback contract for canvas-originated selection."""

    def select_object(self, object_id: str) -> None:
        """Select one object in the editor tree or inspector."""


@dataclass(frozen=True)
class SelectionSyncResult:
    """Result of synchronizing one selection event."""

    session: SessionRecord
    selected_object_id: Optional[str]
    handled: bool = True


class SelectionCoordinator:
    """Synchronize selected canvas objects across editor and canvas sources."""

    def __init__(
        self,
        overlay_manager: CanvasOverlayManager,
        editor_sink: Optional[EditorSelectionSink] = None,
        engine: Optional[CanvasInteractionEngine] = None,
        diagnostic_sink: Optional[DiagnosticSink] = None,
    ) -> None:
        self._overlay_manager = overlay_manager
        self._editor_sink = editor_sink
        self._engine = engine if engine is not None else CanvasInteractionEngine()
        self._diagnostics = diagnostic_sink

    def select_from_editor(self, session: SessionRecord, object_id: str) -> SelectionSyncResult:
        """Apply editor-originated selection to session and canvas overlay state."""

        return self._select(session, object_id, notify_editor=False, source="editor")

    def select_from_canvas(self, session: SessionRecord, object_id: str) -> SelectionSyncResult:
        """Apply canvas-originated selection to session and future editor state."""

        return self._select(session, object_id, notify_editor=True, source="canvas")

    def _select(
        self,
        session: SessionRecord,
        object_id: str,
        notify_editor: bool,
        source: str,
    ) -> SelectionSyncResult:
        canvas_object = find_canvas_object(session, object_id)
        if canvas_object is None or not canvas_object.selectable:
            self._emit("SelectionSyncMismatch", object_id, source, "Selection target missing.")
            return SelectionSyncResult(session=session, selected_object_id=None, handled=False)
        session = self._engine.select_object(session, object_id)
        selected = find_canvas_object(session, object_id)
        if selected is not None:
            self._overlay_manager.select_object(selected)
        if notify_editor and self._editor_sink is not None:
            self._editor_sink.select_object(object_id)
        self._emit("SelectionSynced", object_id, source, "Selection synchronized.")
        return SelectionSyncResult(session=session, selected_object_id=object_id)

    def _emit(self, event_name: str, object_id: str, source: str, message: str) -> None:
        if self._diagnostics is None:
            return
        TraceContext.new(sink=self._diagnostics).with_canvas_object(object_id).emit(
            event_name,
            {
                "message": message,
                "category": "selection_sync",
                "source_component": "SelectionCoordinator",
                "operation": source,
                "related_record_ids": (object_id,),
                "severity": "warning" if event_name.endswith("Mismatch") else "info",
            },
        )

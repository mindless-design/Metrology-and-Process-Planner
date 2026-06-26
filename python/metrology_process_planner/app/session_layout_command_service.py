"""Session current-layout binding command service."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_document_command_results import (
    open_result,
    selection_result,
)
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_command_results import no_document
from metrology_process_planner.app.session_layout_adapter import (
    SessionLayoutAdapter,
    UnavailableSessionLayoutAdapter,
)
from metrology_process_planner.domains.session import (
    SessionRecord,
    SourceLayoutContext,
    WarningRecord,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from metrology_process_planner.workflows.overlays import CanvasOverlayManager


class SessionLayoutCommandService:
    """Translate live-layout binding commands into document updates."""

    def __init__(
        self,
        controller: SessionEditorController,
        layout_adapter: SessionLayoutAdapter | None = None,
        overlay_manager: CanvasOverlayManager | None = None,
    ) -> None:
        self._controller = controller
        self._layout_adapter = (
            layout_adapter if layout_adapter is not None else UnavailableSessionLayoutAdapter()
        )
        self._overlay_manager = overlay_manager

    def bind_current_layout_to_session(self) -> CommandRouteResult:
        """Bind the active document to host-provided current layout metadata."""

        document = self._controller.current_document
        if document is None:
            return no_document(CommandId.BIND_CURRENT_LAYOUT_TO_SESSION, "layout binding")
        if self._controller.current_paths is None:
            return _unsaved_session_result()
        selection = self._layout_adapter.select_current_layout()
        if selection.status != "selected" or selection.source_layout is None:
            return selection_result(
                CommandId.BIND_CURRENT_LAYOUT_TO_SESSION,
                selection.status,
                selection.message,
            )
        self._replace_document_source_layout(selection.source_layout)
        saved = self._controller.save_current_session()
        if saved.document is None:
            return open_result(CommandId.BIND_CURRENT_LAYOUT_TO_SESSION, saved)
        return _bind_success_result(saved, self._restore_overlays(saved.document.session))

    def _replace_document_source_layout(self, current: SourceLayoutContext) -> None:
        document = self._controller.current_document
        assert document is not None
        warnings = _warnings_for_layout_bind(
            document.session.warnings,
            document.session.source_layout,
            current,
        )
        session = replace(document.session, source_layout=current, warnings=warnings)
        rebuilt = SessionDocumentBuilder(mode_registry=self._controller.mode_registry).build(
            session,
            raw_payload=document.raw_payload,
        )
        self._controller.replace_current_document(
            replace(
                rebuilt,
                loaded_path=document.loaded_path,
                revision=document.revision,
                selection=document.selection,
                dirty_state=document.dirty_state,
            )
        )

    def _restore_overlays(self, session: SessionRecord) -> int:
        if self._overlay_manager is None:
            return 0
        canvas_objects = session.canvas_objects
        self._overlay_manager.restore_session(session)
        return len(canvas_objects)


def _unsaved_session_result() -> CommandRouteResult:
    return CommandRouteResult(
        CommandId.BIND_CURRENT_LAYOUT_TO_SESSION,
        "unavailable",
        "Bind Current Layout requires a saved session path.",
        next_ui_hint="Create or open a session.json before binding a live layout.",
    )


def _bind_success_result(saved: Any, restored_count: int) -> CommandRouteResult:
    document = saved.document
    message = "Current layout bound to session."
    if restored_count:
        message = f"{message} Restored {restored_count} overlay(s)."
    return CommandRouteResult(
        CommandId.BIND_CURRENT_LAYOUT_TO_SESSION,
        "success",
        message,
        updated_document_id=document.session.id,
        selected_item_id=document.selection.selected_item_id,
        warning_ids=tuple(warning.id for warning in document.warnings),
    )


def _warnings_for_layout_bind(
    existing: tuple[WarningRecord, ...],
    previous: SourceLayoutContext,
    current: SourceLayoutContext,
) -> tuple[WarningRecord, ...]:
    open_warnings = tuple(
        warning
        for warning in existing
        if not (warning.code == "SOURCE_LAYOUT_MISMATCH" and warning.status == "open")
    )
    mismatch_fields = _layout_mismatch_fields(previous, current)
    if not mismatch_fields:
        return open_warnings
    return open_warnings + (_layout_mismatch_warning(mismatch_fields),)


def _layout_mismatch_warning(mismatch_fields: tuple[str, ...]) -> WarningRecord:
    return WarningRecord(
        id="source-layout-mismatch",
        message="Bound current layout differs from the previous session layout binding.",
        source="source_layout",
        code="SOURCE_LAYOUT_MISMATCH",
        technical_details=", ".join(mismatch_fields),
        repair_suggestion="Review restored overlays against the newly bound layout.",
    )


def _layout_mismatch_fields(
    previous: SourceLayoutContext,
    current: SourceLayoutContext,
) -> tuple[str, ...]:
    fields: list[str] = []
    if previous.layout_path and current.layout_path and previous.layout_path != current.layout_path:
        fields.append("layout_path")
    if _fingerprint_mismatch(previous, current):
        fields.append("layout_fingerprint")
    if previous.top_cell and current.top_cell and previous.top_cell != current.top_cell:
        fields.append("top_cell")
    return tuple(fields)


def _fingerprint_mismatch(previous: SourceLayoutContext, current: SourceLayoutContext) -> bool:
    return bool(
        previous.layout_fingerprint
        and current.layout_fingerprint
        and previous.layout_fingerprint != current.layout_fingerprint
    )

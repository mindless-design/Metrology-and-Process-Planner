"""Dispatch explicit editor actions through application and workflow services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.persistence.process_output_store import ProcessOutputStore
from metrology_process_planner.workflows.editor.adapter_measurement_policy import (
    mode_supports_measurements,
)
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.dispatcher_rendering import (
    _pending_save,
    _regenerate_artifact,
    _save_document,
)
from metrology_process_planner.workflows.editor.dispatcher_results import (
    EditorActionResult as EditorActionResult,
)
from metrology_process_planner.workflows.editor.dispatcher_routes import dispatch_mapped_action
from metrology_process_planner.workflows.editor.dispatcher_support import (
    _rebuild_document,
    _record_id,
)
from metrology_process_planner.workflows.editor.dispatcher_warnings import (
    warning_action_result,
)
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.render_bridge import SessionRenderBridge
from metrology_process_planner.workflows.editor.render_bridge_models import CrossSectionRenderInput
from metrology_process_planner.workflows.editor.store import SessionDocumentStore
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType
from metrology_process_planner.workflows.measurement_review import (
    discard_pending_measurement,
    retake_pending_measurement_line,
)
from metrology_process_planner.workflows.measurement_workflow import (
    begin_measurement_line,
    measurement_parent_unavailable_reason,
)
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService
from metrology_process_planner.workflows.selection import SelectionCoordinator


class EditorActionDispatcher:
    """Route editor actions to workflow and persistence services."""

    def __init__(
        self,
        paths: Optional[SessionPaths] = None,
        document_store: Optional[SessionDocumentStore] = None,
        csv_exporter: Optional[CaptureCsvExporter] = None,
        pending_review: Optional[PendingCaptureReviewService] = None,
        selection_coordinator: Optional[SelectionCoordinator] = None,
        builder: Optional[SessionDocumentBuilder] = None,
        render_bridge: Optional[SessionRenderBridge] = None,
        cross_section_inputs: Optional[Mapping[str, CrossSectionRenderInput]] = None,
        process_output_store: Optional[ProcessOutputStore] = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._paths = paths
        self._mode_registry = mode_registry
        self._store = (
            document_store
            if document_store is not None
            else SessionDocumentStore(mode_registry=mode_registry)
        )
        self._csv = (
            csv_exporter
            if csv_exporter is not None
            else CaptureCsvExporter(mode_registry=mode_registry)
        )
        self._pending = (
            pending_review
            if pending_review is not None
            else PendingCaptureReviewService(mode_registry=mode_registry)
        )
        self._selection = selection_coordinator
        self._builder = (
            builder if builder is not None else SessionDocumentBuilder(mode_registry)
        )
        self._render_bridge = render_bridge
        self._cross_section_inputs = dict(cross_section_inputs or {})
        self._process_output_store = (
            process_output_store if process_output_store is not None else ProcessOutputStore()
        )

    def dispatch(self, document: SessionDocument, action: EditorAction) -> EditorActionResult:
        """Dispatch one editor action and return the updated document result."""

        if not action.enabled:
            return EditorActionResult(
                "unavailable",
                document,
                action.disabled_reason or f"{action.label} is currently unavailable.",
            )
        if routed := dispatch_mapped_action(self, document, action):
            return routed
        if (warning_result := warning_action_result(self, document, action)) is not None:
            return warning_result
        if action.action_type is EditorActionType.EXIT_SESSION:
            return EditorActionResult("success", document, "Session editor exit requested.")
        return EditorActionResult(
            "unavailable",
            document,
            f"{action.label} is not implemented yet.",
        )

    def _save(self, document: SessionDocument) -> EditorActionResult:
        return _save_document(self, document)

    def _pending_save(self, document: SessionDocument, action: EditorAction) -> EditorActionResult:
        return _pending_save(self, document, action)

    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        return _rebuild_document(self, session, document)

    def _regenerate_artifact(
        self,
        document: SessionDocument,
        action: EditorAction,
    ) -> EditorActionResult:
        return _regenerate_artifact(self, document, action)

    def _add_measurement(
        self,
        document: SessionDocument,
        action: EditorAction,
    ) -> EditorActionResult:
        if not mode_supports_measurements(document.session, self._mode_registry):
            return EditorActionResult(
                "unavailable",
                document,
                "The active mode does not support measurements.",
            )
        capture_id = _record_id(document, action.item_id)
        disabled_reason = measurement_parent_unavailable_reason(document.session, capture_id)
        if disabled_reason:
            return EditorActionResult("blocked", document, disabled_reason)
        session = begin_measurement_line(document.session, capture_id)
        if not _measurement_line_is_armed(session, capture_id):
            return EditorActionResult(
                "blocked",
                document,
                "Measurements require a saved canvas box for this capture.",
            )
        return EditorActionResult(
            "success",
            self._rebuild(session, document),
            "Armed measurement line capture.",
        )

    def _retake_measurement(
        self,
        document: SessionDocument,
        action: EditorAction,
    ) -> EditorActionResult:
        measurement_id = _record_id(document, action.item_id)
        session = retake_pending_measurement_line(document.session, measurement_id)
        return EditorActionResult(
            "success",
            self._rebuild(session, document),
            "Retaking measurement line.",
        )

    def _discard_measurement(
        self,
        document: SessionDocument,
        action: EditorAction,
    ) -> EditorActionResult:
        measurement_id = _record_id(document, action.item_id)
        session = discard_pending_measurement(document.session, measurement_id)
        return EditorActionResult(
            "success",
            self._rebuild(session, document),
            "Discarded pending measurement.",
        )


def _measurement_line_is_armed(session: SessionRecord, capture_id: str) -> bool:
    return (
        session.workflow.active
        and session.workflow.stage == "measurement_line"
        and session.workflow.pending_item_ref == f"capture:{capture_id}"
    )

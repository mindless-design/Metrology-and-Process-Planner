"""Rendering-aware editor action handlers."""

from __future__ import annotations

from typing import Optional, Protocol

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.dispatcher_rendering_artifacts import (
    regenerate_artifact as _regenerate_artifact_action,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import (
    _empty_context,
    _payload_value,
    _rebuild_document,
    _record_id,
    _with_session,
)
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.editing import apply_metadata_edits
from metrology_process_planner.workflows.editor.render_bridge import SessionRenderBridge
from metrology_process_planner.workflows.editor.render_bridge_models import (
    CrossSectionRenderInput,
    DrawingOwnerRef,
    RenderRefreshRequest,
    RenderRefreshResult,
    RenderTarget,
)
from metrology_process_planner.workflows.editor.store import SessionDocumentStore
from metrology_process_planner.workflows.editor.view_models import EditorAction
from metrology_process_planner.workflows.measurement_completion import (
    measurement_completion_prompt,
    pending_measurement_count,
)
from metrology_process_planner.workflows.measurement_validation import (
    measurement_metadata_edit_errors,
    measurement_validation_errors,
)
from metrology_process_planner.workflows.measurement_workflow import save_pending_measurements
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService


class _RenderingDispatcher(Protocol):
    """Editor dispatcher capabilities required by rendering-aware actions."""

    _paths: Optional[SessionPaths]
    _store: SessionDocumentStore
    _builder: SessionDocumentBuilder
    _pending: PendingCaptureReviewService
    _render_bridge: Optional[SessionRenderBridge]
    _cross_section_inputs: dict[str, CrossSectionRenderInput]
    _mode_registry: ModeRegistry | None

    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after workflow state changes."""


def _save_document(
    dispatcher: _RenderingDispatcher,
    document: SessionDocument,
) -> EditorActionResult:
    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    original = document
    pending_measurements_before_save = pending_measurement_count(document.session)
    if edit_errors := measurement_metadata_edit_errors(document):
        return EditorActionResult("blocked", document, "; ".join(edit_errors))
    document = apply_metadata_edits(document, dispatcher._mode_registry)
    if errors := measurement_validation_errors(document.session):
        return EditorActionResult("blocked", document, "; ".join(errors))
    document = _with_session(
        dispatcher,
        document,
        save_pending_measurements(document.session, dispatcher._mode_registry),
    )
    render_result = _refresh_on_save(dispatcher, document.session)
    document = _with_session(dispatcher, document, render_result.session)
    try:
        saved = dispatcher._store.save(document, dispatcher._paths)
    except (OSError, ValueError) as exc:
        return EditorActionResult("error", original, str(exc))
    saved = _with_session(dispatcher, original, saved.session)
    status = "success" if render_result.status == "success" else render_result.status
    message = "Saved session edits."
    if render_result.message:
        message = f"{message} {render_result.message}"
    prompt = None
    if pending_measurements_before_save and pending_measurement_count(saved.session) == 0:
        prompt = measurement_completion_prompt(saved.session)
    return EditorActionResult(status, saved, message, dispatcher._paths.session_json, prompt)


def _pending_save(
    dispatcher: _RenderingDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    document = apply_metadata_edits(document, dispatcher._mode_registry)
    pending_id = _record_id(document, action.item_id)
    pending_metadata = _pending_metadata(document.session, pending_id)
    label = _payload_value(action, "label") or pending_metadata.get("label", "")
    notes = _payload_value(action, "notes") or pending_metadata.get("notes", "")
    replacement_id = pending_metadata.get("replacement_for", "")
    before_capture_ids = {capture.id for capture in document.session.captures}
    result = dispatcher._pending.save_pending_box(
        document.session,
        _empty_context(),
        pending_id,
        label=label,
        notes=notes,
    )
    session = result.session
    render_result = None
    refresh_capture_id = replacement_id or _new_capture_id(before_capture_ids, session)
    if refresh_capture_id is not None and dispatcher._paths is not None:
        render_result = _refresh_targets(
            dispatcher,
            session,
            (RenderTarget(DrawingOwnerRef("capture", refresh_capture_id)),),
        )
        session = render_result.session
    message = "Saved pending capture."
    status = "success"
    if render_result is not None and render_result.status != "success":
        status = render_result.status
        message = f"{message} {render_result.message}"
    return EditorActionResult(status, _rebuild_document(dispatcher, session, document), message)


def _regenerate_artifact(
    dispatcher: _RenderingDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    return _regenerate_artifact_action(dispatcher, document, action)


def _refresh_on_save(
    dispatcher: _RenderingDispatcher,
    session: SessionRecord,
) -> RenderRefreshResult:
    return _render_bridge_for_paths(dispatcher).refresh(
        session,
        RenderRefreshRequest(refresh_all_captures=True, refresh_all_measurements=True),
    )


def _refresh_targets(
    dispatcher: _RenderingDispatcher,
    session: SessionRecord,
    targets: tuple[RenderTarget, ...],
) -> RenderRefreshResult:
    return _render_bridge_for_paths(dispatcher).refresh(
        session,
        RenderRefreshRequest(targets=targets),
    )


def _render_bridge_for_paths(dispatcher: _RenderingDispatcher) -> SessionRenderBridge:
    if dispatcher._render_bridge is not None:
        return dispatcher._render_bridge
    if dispatcher._paths is None:
        raise RuntimeError("Session paths are required for rendering.")
    return SessionRenderBridge(dispatcher._paths, mode_registry=dispatcher._mode_registry)


def _pending_metadata(session: SessionRecord, pending_id: str) -> dict[str, str]:
    for pending in session.pending_captures:
        if pending.id == pending_id:
            return {key: str(value) for key, value in dict(pending.metadata or {}).items()}
    return {}


def _new_capture_id(previous_ids: set[str], session: SessionRecord) -> Optional[str]:
    for capture in session.captures:
        if capture.id not in previous_ids:
            return capture.id
    return None

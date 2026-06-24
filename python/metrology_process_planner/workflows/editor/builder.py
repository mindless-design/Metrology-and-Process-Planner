"""Build normalized editor documents from canonical session records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any, Optional

from metrology_process_planner.domains.session import CaptureRecord, SessionRecord
from metrology_process_planner.workflows.editor.builder_artifact_refs import (
    _artifact_refs,
    _artifact_refs_for_owner,
)
from metrology_process_planner.workflows.editor.builder_canvas import (
    capture_canvas_ids,
    pending_canvas_ids,
)
from metrology_process_planner.workflows.editor.builder_drawings import (
    artifact_owned_drawing_items,
)
from metrology_process_planner.workflows.editor.builder_features import (
    feature_items_for_capture,
)
from metrology_process_planner.workflows.editor.builder_measurements import measurement_item_for
from metrology_process_planner.workflows.editor.builder_views import (
    _grid_item,
    _groups,
    _process_output_item,
    _report_item,
    _warning_item,
    _warning_view_models,
)
from metrology_process_planner.workflows.editor.document import (
    EditorSelectionState,
    SessionDocument,
    SessionItem,
    SessionItemKind,
)
from metrology_process_planner.workflows.editor.references import RecordRef
from metrology_process_planner.workflows.editor.view_models import WarningViewModel


class SessionDocumentBuilder:
    """Build a normalized session editor document and item indexes."""

    def build(
        self,
        session: SessionRecord,
        raw_payload: Optional[Mapping[str, Any]] = None,
    ) -> SessionDocument:
        """Return an editor document for a canonical session record."""

        warnings = _warning_view_models(session)
        warning_artifacts = {
            warning.artifact_path: warning for warning in warnings if warning.artifact_path
        }
        items = _attach_children(_session_items(session, warnings, warning_artifacts))
        selected = _default_selection(session)
        return SessionDocument(
            session=session,
            raw_payload=dict(raw_payload or {}),
            items_by_id=items,
            root_item_ids=tuple(items),
            navigator_groups=_groups(items),
            selection=selected,
            warning_view_models=warnings,
            pending_capture_item_id=selected.selected_item_id if session.pending_captures else None,
        )


def _add(items: dict[str, SessionItem], item: SessionItem) -> None:
    items[item.item_id] = item


def _session_items(
    session: SessionRecord,
    warnings: tuple[WarningViewModel, ...],
    warning_artifacts: Mapping[str, WarningViewModel],
) -> dict[str, SessionItem]:
    items: dict[str, SessionItem] = {}
    _add(items, _dashboard_item(session))
    _add(items, _setup_item())
    _add_record_items(items, session, warning_artifacts)
    for warning in warnings:
        _add(items, _warning_item(warning))
    return items


def _add_record_items(
    items: dict[str, SessionItem],
    session: SessionRecord,
    warning_artifacts: Mapping[str, WarningViewModel],
) -> None:
    for pending in session.pending_captures:
        _add(items, _pending_item(session, pending.id, warning_artifacts))
    for capture in session.captures:
        _add(items, _capture_item(session, capture))
        for feature_item in feature_items_for_capture(session, capture):
            _add(items, feature_item)
        for measurement in capture.measurements:
            _add(items, measurement_item_for(session, capture.id, measurement))
    for dataset in session.grid_datasets:
        _add(items, _grid_item(session, dataset.id, dataset.label))
    for item in artifact_owned_drawing_items(session):
        _add(items, item)
    for report in session.reports:
        _add(items, _report_item(session, report.id, report.label or report.report_type))
    for output in session.process_outputs:
        _add(items, _process_output_item(session, output.id, output.label))


def _dashboard_item(session: SessionRecord) -> SessionItem:
    return SessionItem(
        item_id="dashboard",
        kind=SessionItemKind.DASHBOARD,
        label=session.name,
        role="dashboard",
    )

def _setup_item() -> SessionItem:
    return SessionItem(
        item_id="setup",
        kind=SessionItemKind.SETUP,
        label="Setup",
        role="setup",
    )

def _pending_item(
    session: SessionRecord,
    pending_id: str,
    warning_artifacts: Mapping[str, WarningViewModel],
) -> SessionItem:
    pending = next(item for item in session.pending_captures if item.id == pending_id)
    artifact_refs = _artifact_refs(
        (("crop", pending.image_artifact_path),),
        warning_artifacts,
    )
    return SessionItem(
        item_id=f"pending:{pending.id}",
        kind=SessionItemKind.PENDING_CAPTURE,
        label=f"Pending Capture {pending.id}",
        role="pending_capture",
        status="pending",
        parent_id=pending.parent_id,
        record_ref=RecordRef("pending_capture", pending.id, pending.parent_id),
        canvas_object_ids=pending_canvas_ids(session, pending.canvas_object_id),
        artifact_refs=artifact_refs,
    )


def _capture_item(
    session: SessionRecord,
    capture: CaptureRecord,
) -> SessionItem:
    canvas_ids = capture_canvas_ids(session, capture.id)
    artifact_refs = _artifact_refs_for_owner(session, "capture", capture.id)
    return SessionItem(
        item_id=f"capture:{capture.id}",
        kind=SessionItemKind.SAVED_CAPTURE,
        label=capture.label or capture.id,
        role=capture.type,
        record_ref=RecordRef("capture", capture.id),
        canvas_object_ids=canvas_ids,
        artifact_refs=artifact_refs,
    )


def _attach_children(items: dict[str, SessionItem]) -> dict[str, SessionItem]:
    child_map: dict[str, list[str]] = {}
    for item in items.values():
        if item.parent_id:
            child_map.setdefault(item.parent_id, []).append(item.item_id)
    return {
        item_id: replace(item, child_ids=tuple(child_map.get(item_id, ())))
        for item_id, item in items.items()
    }


def _default_selection(session: SessionRecord) -> EditorSelectionState:
    if session.pending_captures:
        pending = session.pending_captures[0]
        return EditorSelectionState(
            selected_item_id=f"pending:{pending.id}",
            selected_canvas_object_ids=pending_canvas_ids(session, pending.canvas_object_id),
        )
    return EditorSelectionState()

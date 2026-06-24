"""Measurement editor item builders."""

from __future__ import annotations

from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.editor.builder_artifact_refs import (
    _artifact_refs_for_owner,
)
from metrology_process_planner.workflows.editor.document import SessionItem, SessionItemKind
from metrology_process_planner.workflows.editor.references import RecordRef


def measurement_item_for(
    session: SessionRecord,
    capture_id: str,
    measurement: MeasurementRecord,
) -> SessionItem:
    """Return an editor item for a nested measurement record."""

    status = str(dict(measurement.metadata or {}).get("workflow_state", "saved"))
    canvas_ids = tuple(
        item.id for item in session.canvas_objects if item.record_id == measurement.id
    )
    return SessionItem(
        item_id=f"measurement:{measurement.id}",
        kind=SessionItemKind.MEASUREMENT,
        label=measurement.label or measurement.id,
        role="measurement",
        status=status,
        parent_id=f"capture:{capture_id}",
        record_ref=RecordRef("measurement", measurement.id, capture_id),
        canvas_object_ids=canvas_ids,
        artifact_refs=_artifact_refs_for_owner(session, "measurement", measurement.id),
    )

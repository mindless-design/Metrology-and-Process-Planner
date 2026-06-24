"""Composite capture feature editor item builders."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.session import CaptureRecord, SessionRecord
from metrology_process_planner.workflows.editor.builder_artifact_refs import (
    _artifact_refs_for_owner,
)
from metrology_process_planner.workflows.editor.document import SessionItem, SessionItemKind
from metrology_process_planner.workflows.editor.references import ArtifactRef, RecordRef


def feature_items_for_capture(
    session: SessionRecord,
    capture: CaptureRecord,
) -> tuple[SessionItem, ...]:
    """Return editor child items for composite geometry features."""

    return tuple(_feature_item(session, capture, feature) for feature in capture.geometry.features)


def _feature_item(
    session: SessionRecord,
    capture: CaptureRecord,
    feature: Mapping[str, object],
) -> SessionItem:
    feature_id = str(feature.get("id", ""))
    role = str(feature.get("role", feature.get("kind", "feature")))
    return SessionItem(
        item_id=f"feature:{feature_id}",
        kind=SessionItemKind.FEATURE,
        label=str(feature.get("label", role.replace("_", " ").title())),
        role=role,
        parent_id=f"capture:{capture.id}",
        record_ref=RecordRef("feature", feature_id, capture.id),
        canvas_object_ids=tuple(
            item.id for item in session.canvas_objects if item.record_id == feature_id
        ),
        artifact_refs=_feature_artifacts(session, capture.id),
    )


def _feature_artifacts(
    session: SessionRecord,
    capture_id: str,
) -> tuple[ArtifactRef, ...]:
    return tuple(
        artifact
        for artifact in _artifact_refs_for_owner(session, "capture", capture_id)
        if artifact.artifact_type == "layout_annotation"
    )

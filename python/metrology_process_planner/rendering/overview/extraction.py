"""Label target extraction from canonical session records."""

from __future__ import annotations

from collections.abc import Iterable

from metrology_process_planner.domains.capture.capture_geometry import CaptureGeometry
from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import CaptureRecord, GeometryKind, SessionRecord
from metrology_process_planner.rendering.overview.geometry import (
    box_from_geometry,
    padded_point_box,
)
from metrology_process_planner.rendering.overview.models import LabelTarget, UserLabelRecord
from metrology_process_planner.rendering.overview.user_labels import user_labels_from_session


def extract_label_targets(session: SessionRecord) -> tuple[LabelTarget, ...]:
    """Extract overview targets from captures, measurements, features, and user labels."""

    targets: list[LabelTarget] = []
    for capture in session.captures:
        if capture.status in {"hidden", "superseded"}:
            continue
        target = _capture_target(capture)
        if target is not None:
            targets.append(target)
        targets.extend(_measurement_targets(capture))
        targets.extend(_feature_targets(capture))
    targets.extend(_user_label_targets(user_labels_from_session(session)))
    return tuple(targets)


def _capture_target(capture: CaptureRecord) -> LabelTarget | None:
    bbox = _geometry_bbox(capture.geometry)
    if bbox is None:
        return None
    return LabelTarget(
        target_id=f"target-capture-{capture.id}",
        target_type="capture_box",
        source_item_id=capture.id,
        geometry=capture.geometry.to_dict(),
        anchor_point=_anchor(capture.geometry, bbox),
        bbox=bbox,
        priority=70 if capture.warning_ids else 50,
        label_role=capture.role or "capture",
        status=capture.status,
        warning_ids=capture.warning_ids,
        style_hint=capture.type,
        metadata={"label": capture.label, "notes": capture.notes, "sequence": capture.sequence},
    )


def _measurement_targets(capture: CaptureRecord) -> Iterable[LabelTarget]:
    for measurement in capture.measurements:
        yield _measurement_target(capture.id, measurement)


def _measurement_target(capture_id: str, measurement: MeasurementRecord) -> LabelTarget:
    bbox = Box(
        min(measurement.start.x, measurement.end.x),
        min(measurement.start.y, measurement.end.y),
        max(measurement.start.x, measurement.end.x),
        max(measurement.start.y, measurement.end.y),
    )
    anchor = Point(
        (measurement.start.x + measurement.end.x) / 2.0,
        (measurement.start.y + measurement.end.y) / 2.0,
    )
    return LabelTarget(
        target_id=f"target-measurement-{measurement.id}",
        target_type="measurement_line",
        source_item_id=measurement.id,
        geometry={
            "kind": "line",
            "start": measurement.start.to_dict(),
            "end": measurement.end.to_dict(),
        },
        anchor_point=anchor,
        bbox=bbox,
        priority=75 if measurement.warning_ids else 60,
        label_role="measurement",
        warning_ids=measurement.warning_ids,
        style_hint="measurement",
        metadata={
            "capture_id": capture_id,
            "label": measurement.label,
            "target": measurement.target,
            "length": measurement.measured_length,
            "notes": measurement.notes,
        },
    )


def _feature_targets(capture: CaptureRecord) -> Iterable[LabelTarget]:
    for index, feature in enumerate(capture.geometry.features):
        kind = str(feature.get("kind", feature.get("type", "feature")))
        bbox = box_from_geometry(feature)
        if bbox is None:
            continue
        yield LabelTarget(
            target_id=f"target-feature-{capture.id}-{index}",
            target_type=_feature_target_type(kind),
            source_item_id=capture.id,
            geometry=dict(feature),
            anchor_point=bbox.center,
            bbox=bbox,
            priority=65,
            label_role=kind,
            style_hint=kind,
            metadata={"capture_id": capture.id, "label": str(feature.get("label", kind))},
        )


def _user_label_targets(labels: Iterable[UserLabelRecord]) -> Iterable[LabelTarget]:
    for label in labels:
        if label.hidden or not label.include_in_overview:
            continue
        bbox = box_from_geometry(label.geometry)
        if bbox is None:
            continue
        yield LabelTarget(
            target_id=f"target-user-label-{label.label_id}",
            target_type=f"user_{label.geometry.get('kind', 'note')}",
            source_item_id=label.label_id,
            geometry=dict(label.geometry),
            anchor_point=bbox.center,
            bbox=bbox,
            priority=label.priority,
            label_role="user_label",
            warning_ids=label.warning_ids,
            style_hint=label.style,
            metadata={"title": label.title, "notes": label.notes},
        )


def _geometry_bbox(geometry: CaptureGeometry) -> Box | None:
    if geometry.bounds is not None:
        return geometry.bounds.normalized()
    if geometry.kind is GeometryKind.POINT and geometry.point is not None:
        return padded_point_box(geometry.point)
    if (
        geometry.kind is GeometryKind.LINE
        and geometry.start is not None
        and geometry.end is not None
    ):
        return Box(
            min(geometry.start.x, geometry.end.x),
            min(geometry.start.y, geometry.end.y),
            max(geometry.start.x, geometry.end.x),
            max(geometry.start.y, geometry.end.y),
        )
    return None


def _anchor(geometry: CaptureGeometry, bbox: Box) -> Point:
    if geometry.kind is GeometryKind.POINT and geometry.point is not None:
        return geometry.point
    if (
        geometry.kind is GeometryKind.LINE
        and geometry.start is not None
        and geometry.end is not None
    ):
        return Point(
            (geometry.start.x + geometry.end.x) / 2.0,
            (geometry.start.y + geometry.end.y) / 2.0,
        )
    return bbox.center


def _feature_target_type(kind: str) -> str:
    mapping = {
        "profilometry_line": "profilometry_line",
        "ellipsometry_point": "ellipsometry_point",
        "fib_cut": "fib_cut_line",
        "fib_cut_line": "fib_cut_line",
        "process_flow_site": "process_flow_site",
        "cad_review_issue": "cad_review_issue",
    }
    return mapping.get(kind, kind)

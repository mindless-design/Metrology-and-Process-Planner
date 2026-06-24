"""Child feature capture operations for compound workflows."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import CanvasObjectType, SessionRecord
from metrology_process_planner.workflows.canvas_interaction_helpers import next_id
from metrology_process_planner.workflows.compound_capture_models import (
    CompoundCaptureRequest,
    InnerFeatureDefinition,
)
from metrology_process_planner.workflows.compound_capture_pending import (
    feature_ids,
    required_pending,
    with_child_feature,
)
from metrology_process_planner.workflows.compound_capture_records import required_bounds
from metrology_process_planner.workflows.compound_capture_support import line_warnings


def add_line_feature(
    session: SessionRecord,
    pending_id: str,
    start: Point,
    end: Point,
    request: CompoundCaptureRequest,
    metadata: dict[str, Any] | None = None,
) -> SessionRecord:
    """Add a validated line feature to a pending compound capture."""

    if request.child_kind != "line":
        raise ValueError("Line feature requires a site_then_line request.")
    pending = required_pending(session, pending_id)
    warnings = line_warnings(required_bounds(pending), start, end, metadata or {})
    if warnings:
        raise ValueError("; ".join(warnings))
    feature = InnerFeatureDefinition(
        next_id("feat", feature_ids(session)),
        request.child_label or "Line",
        request.child_role,
        "line",
        _line_geometry(start, end),
    )
    object_type = CanvasObjectType(request.child_canvas_object_type or CanvasObjectType.LINE.value)
    return with_child_feature(session, pending, request, feature, object_type)


def add_point_feature(
    session: SessionRecord,
    pending_id: str,
    point: Point,
    request: CompoundCaptureRequest,
) -> SessionRecord:
    """Add a validated point feature to a pending compound capture."""

    if request.child_kind != "point":
        raise ValueError("Point feature requires a site_then_point request.")
    pending = required_pending(session, pending_id)
    if not required_bounds(pending).contains_point(point):
        raise ValueError("Point must be inside the parent site box.")
    feature = InnerFeatureDefinition(
        next_id("feat", feature_ids(session)),
        request.child_label or "Point",
        request.child_role,
        "point",
        {"shape": "point", "point": point.to_dict(), "units": "layout"},
    )
    object_type = CanvasObjectType(request.child_canvas_object_type or CanvasObjectType.POINT.value)
    return with_child_feature(session, pending, request, feature, object_type)


def _line_geometry(start: Point, end: Point) -> dict[str, object]:
    return {
        "shape": "line",
        "start": start.to_dict(),
        "end": end.to_dict(),
        "length": start.distance_to(end),
        "units": "layout",
    }

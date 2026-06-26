"""Save-time validation for shared compound capture workflows."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.workflows.compound_capture_models import (
    PendingCompositeCapture,
)
from metrology_process_planner.workflows.compound_capture_records import required_bounds
from metrology_process_planner.workflows.compound_capture_support import (
    optional_float,
    process_outputs_enabled,
)


def composite_save_warnings(
    session: SessionRecord,
    composite: PendingCompositeCapture,
    metadata: Mapping[str, object],
) -> tuple[str, ...]:
    """Return save-blocking validation messages for a pending composite."""

    warnings: list[str] = []
    warnings.extend(_mode_warnings(composite))
    warnings.extend(_parent_warnings(session, composite))
    warnings.extend(_feature_warnings(session, composite))
    warnings.extend(_metadata_warnings(composite, metadata))
    return tuple(warnings)


def _mode_warnings(composite: PendingCompositeCapture) -> tuple[str, ...]:
    request = composite.request
    warnings: list[str] = []
    if not request.mode_id:
        warnings.append("Compound capture mode id is required.")
    if request.sequence_type not in {"site_then_line", "site_then_point"}:
        warnings.append(f"Unsupported compound sequence {request.sequence_type}.")
    expected_kind = "line" if request.sequence_type == "site_then_line" else "point"
    if request.child_kind != expected_kind:
        warnings.append(f"Mode {request.mode_id} requires a {expected_kind} child feature.")
    required = {
        "annotation artifact role": request.annotation_role,
        "saved capture type": request.saved_capture_type,
        "extension key": request.extension_key,
        "feature id field": request.feature_id_field,
    }
    if process_outputs_enabled(request):
        required["process output key"] = request.process_output_key
    for label, value in required.items():
        if not value:
            warnings.append(f"Mode {request.mode_id} missing {label}.")
    return tuple(warnings)


def _parent_warnings(
    session: SessionRecord,
    composite: PendingCompositeCapture,
) -> tuple[str, ...]:
    pending = next(
        (item for item in session.pending_captures if item.id == composite.parent.pending_id),
        None,
    )
    if pending is None:
        return (f"Pending parent {composite.parent.pending_id} was not found.",)
    try:
        required_bounds(pending)
    except ValueError as exc:
        return (str(exc),)
    return ()


def _feature_warnings(
    session: SessionRecord,
    composite: PendingCompositeCapture,
) -> tuple[str, ...]:
    feature = composite.feature
    if feature is None:
        return ("Composite capture requires an inner feature before save.",)
    warnings: list[str] = []
    request = composite.request
    expected_kind = "line" if request.sequence_type == "site_then_line" else "point"
    if feature.kind != expected_kind:
        warnings.append(f"Inner feature must be a {expected_kind}.")
    if feature.role != request.child_role:
        warnings.append(f"Inner feature role must be {request.child_role}.")
    if feature.id in _saved_feature_ids(session):
        warnings.append(f"Inner feature id {feature.id} is already used.")
    warnings.extend(_geometry_warnings(session, composite))
    return tuple(warnings)


def _geometry_warnings(
    session: SessionRecord,
    composite: PendingCompositeCapture,
) -> tuple[str, ...]:
    pending = next(
        (item for item in session.pending_captures if item.id == composite.parent.pending_id),
        None,
    )
    if pending is None:
        return ()
    bounds = required_bounds(pending)
    feature = composite.feature
    assert feature is not None
    geometry = dict(feature.geometry)
    if feature.kind == "line":
        start = Point.from_dict(geometry["start"])
        end = Point.from_dict(geometry["end"])
        warnings: list[str] = []
        if start == end:
            warnings.append("Line length must be greater than zero.")
        if not bounds.contains_segment(start, end):
            warnings.append("Line endpoints must be inside the parent site box.")
        return tuple(warnings)
    if feature.kind == "point":
        point = Point.from_dict(geometry["point"])
        if not bounds.contains_point(point):
            return ("Point must be inside the parent site box.",)
        return ()
    return (f"Unsupported inner feature kind {feature.kind}.",)


def _metadata_warnings(
    composite: PendingCompositeCapture,
    metadata: Mapping[str, object],
) -> tuple[str, ...]:
    if composite.request.sequence_type == "site_then_line":
        return _line_metadata_warnings(metadata)
    if composite.request.sequence_type == "site_then_point":
        return ()
    return (f"Unsupported compound sequence {composite.request.sequence_type}.",)


def _line_metadata_warnings(metadata: Mapping[str, object]) -> tuple[str, ...]:
    warnings: list[str] = []
    target = _optional_number(metadata, "target", warnings)
    lsl = _optional_number(metadata, "lsl", warnings)
    usl = _optional_number(metadata, "usl", warnings)
    if target is not None and lsl is not None and usl is not None and not lsl <= target <= usl:
        warnings.append("Specification limits must satisfy LSL <= target <= USL.")
    warnings.extend(_positive_number(metadata, "line_weight_px", "Line weight"))
    warnings.extend(_positive_number(metadata, "text_scale", "Text scale"))
    warnings.extend(_color_warnings(metadata.get("line_color")))
    return tuple(warnings)


def _optional_number(
    metadata: Mapping[str, object],
    key: str,
    warnings: list[str],
) -> float | None:
    try:
        return optional_float(metadata.get(key))
    except (TypeError, ValueError):
        warnings.append(f"{key} must be a number.")
        return None


def _positive_number(
    metadata: Mapping[str, object],
    key: str,
    label: str,
) -> tuple[str, ...]:
    value = metadata.get(key)
    if value in {None, ""}:
        return ()
    try:
        number = optional_float(value)
    except (TypeError, ValueError):
        return (f"{label} must be a number.",)
    if number is None or number <= 0:
        return (f"{label} must be greater than zero.",)
    return ()


def _color_warnings(value: object) -> tuple[str, ...]:
    if value in {None, ""}:
        return ()
    text = str(value)
    hex_digits = text[1:]
    if text.startswith("#") and len(hex_digits) in {3, 6}:
        try:
            int(hex_digits, 16)
        except ValueError:
            return ("Line color must be a hex color.",)
        return ()
    return ("Line color must be a hex color.",)


def _saved_feature_ids(session: SessionRecord) -> set[str]:
    return {
        str(feature.get("id", ""))
        for capture in session.captures
        for feature in capture.geometry.features
    }

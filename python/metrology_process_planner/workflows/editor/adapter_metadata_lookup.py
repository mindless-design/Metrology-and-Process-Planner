"""Record lookup helpers for editor metadata adapters."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import CaptureRecord, PendingCapture, SessionRecord


def capture_by_id(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    """Return the capture with the requested ID."""

    for capture in session.captures:
        if capture.id == capture_id:
            return capture
    return None


def pending_by_id(session: SessionRecord, pending_id: str) -> PendingCapture | None:
    """Return the pending capture with the requested ID."""

    for pending in session.pending_captures:
        if pending.id == pending_id:
            return pending
    return None


def measurement_by_id(session: SessionRecord, measurement_id: str) -> MeasurementRecord | None:
    """Return a nested measurement with the requested ID."""

    for capture in session.captures:
        for measurement in capture.measurements:
            if measurement.id == measurement_id:
                return measurement
    return None


def feature_by_id(session: SessionRecord, feature_id: str) -> dict[str, object] | None:
    """Return a capture geometry feature with the requested ID."""

    for capture in session.captures:
        for feature in capture.geometry.features:
            if str(feature.get("id", "")) == feature_id:
                return dict(feature)
    return None


def mapping(value: object) -> dict[str, object]:
    """Return a plain mapping for object-typed extension fields."""

    if isinstance(value, Mapping):
        return dict(value)
    return {}


def optional_number(value: float | None) -> str:
    """Return an editor string for an optional numeric value."""

    return "" if value is None else str(value)

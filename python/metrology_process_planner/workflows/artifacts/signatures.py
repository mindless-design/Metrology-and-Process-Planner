"""Lightweight dependency signatures for artifact freshness checks."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any

from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import CaptureRecord, ModeRegistry, SessionRecord
from metrology_process_planner.workflows.artifacts.signature_visibility import (
    visible_session_data,
)


def current_signature(
    session: SessionRecord,
    kind: str,
    item_id: str,
    mode_registry: ModeRegistry | None = None,
) -> str:
    """Return the current lightweight signature for a known dependency."""

    value = _dependency_value(session, kind, item_id, mode_registry)
    if value is None:
        return ""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def owner_exists(session: SessionRecord, owner_type: str, owner_id: str) -> bool:
    """Return whether an artifact owner record is present in the session."""

    owners = {
        "capture": _capture_ids(session),
        "measurement": _measurement_ids(session),
        "grid_dataset": {dataset.id for dataset in session.grid_datasets},
        "process_output": {output.id for output in session.process_outputs},
        "report": {report.id for report in session.reports},
    }
    if owner_type in {"session", "report_collection"}:
        return owner_id in {"", session.id}
    return owner_id in owners.get(owner_type, {owner_id} if owner_type and owner_id else set())


def dependency_exists(session: SessionRecord, kind: str, item_id: str) -> bool:
    """Return whether a dependency reference points at existing session data."""

    base_id = _base_id(item_id)
    if kind in {"recipe_context", "recipe"}:
        return bool(session.process_context.recipe_path or session.process_context.recipe_id)
    if kind == "source_layout":
        return bool(session.source_layout.layout_path or session.source_layout.layout_fingerprint)
    if kind in {"generator_version", "render_profile", "mode_definition"}:
        return True
    dependency_sets = {
        "artifact": set(session.artifacts or {}),
        "solver_result": {output.id for output in session.process_outputs},
        "capture": _capture_ids(session),
        "measurement": _measurement_ids(session),
    }
    dependency_type = _dependency_type(kind)
    return base_id in dependency_sets.get(dependency_type, {base_id})


def _dependency_value(
    session: SessionRecord,
    kind: str,
    item_id: str,
    mode_registry: ModeRegistry | None,
) -> Any:
    handlers: Mapping[str, Callable[[SessionRecord, str], Any]] = {
        "session_data": lambda source, _item_id: visible_session_data(
            source,
            mode_registry,
        ),
        "capture_geometry": _capture_geometry_value,
        "capture_metadata": _capture_metadata_value,
        "measurement_geometry": _measurement_geometry_value,
        "measurement_metadata": _measurement_metadata_value,
        "annotation_spec": _annotation_spec_value,
        "recipe_context": lambda source, _item_id: source.process_context.to_dict(),
        "render_profile": lambda source, _item_id: source.process_context.render_profile,
        "source_layout": lambda source, _item_id: source.source_layout.to_dict(),
        "generator_version": lambda _source, dependency_id: dependency_id,
    }
    handler = handlers.get(kind)
    return None if handler is None else handler(session, item_id)


def _capture_geometry_value(session: SessionRecord, item_id: str) -> Any:
    capture = _capture(session, _base_id(item_id))
    return capture.geometry.to_dict() if capture else None


def _capture_metadata_value(session: SessionRecord, item_id: str) -> Any:
    capture = _capture(session, _base_id(item_id))
    return _capture_metadata(capture) if capture else None


def _measurement_geometry_value(session: SessionRecord, item_id: str) -> Any:
    measurement = _measurement(session, _base_id(item_id))
    return _measurement_geometry(measurement) if measurement else None


def _measurement_metadata_value(session: SessionRecord, item_id: str) -> Any:
    measurement = _measurement(session, _base_id(item_id))
    return _mapping_value(measurement.metadata) if measurement else None


def _annotation_spec_value(session: SessionRecord, item_id: str) -> Any:
    measurement = _measurement(session, _base_id(item_id))
    return _annotation_spec(measurement) if measurement else None


def _dependency_type(kind: str) -> str:
    if kind.startswith("capture"):
        return "capture"
    if kind.startswith("measurement"):
        return "measurement"
    return kind


def _capture_ids(session: SessionRecord) -> set[str]:
    return {capture.id for capture in session.captures}


def _measurement_ids(session: SessionRecord) -> set[str]:
    return {
        measurement.id
        for capture in session.captures
        for measurement in capture.measurements
    }


def _capture(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    return next((capture for capture in session.captures if capture.id == capture_id), None)


def _measurement(session: SessionRecord, measurement_id: str) -> MeasurementRecord | None:
    return next(
        (
            measurement
            for capture in session.captures
            for measurement in capture.measurements
            if measurement.id == measurement_id
        ),
        None,
    )


def _capture_metadata(capture: Any) -> dict[str, Any]:
    return {
        "modified_at": capture.modified_at,
        "notes": capture.notes,
        "metadata": _mapping_value(capture.metadata),
        "annotations": _mapping_value(capture.annotations),
    }


def _measurement_geometry(measurement: Any) -> dict[str, Any]:
    return {"start": measurement.start.to_dict(), "end": measurement.end.to_dict()}


def _annotation_spec(measurement: Any) -> dict[str, Any]:
    return {
        "annotation_color": measurement.annotation_color,
        "line_weight": measurement.line_weight,
        "edge_detection_convention": measurement.edge_detection_convention,
    }


def _mapping_value(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


def _base_id(item_id: str) -> str:
    return item_id.split(".", 1)[0]

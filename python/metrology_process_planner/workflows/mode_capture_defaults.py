"""Mode-aware defaults for generic pending capture promotion."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.modes.mode_registry import ModeDefinition
from metrology_process_planner.domains.session import ModeRegistry, PendingCapture, SessionRecord
from metrology_process_planner.workflows.cad_review_metadata import (
    normalized_cad_review_metadata,
)


@dataclass(frozen=True)
class CaptureDefaults:
    """Resolved capture values for pending capture save."""

    sequence: int
    label: str
    role: str
    capture_type: str
    metadata: dict[str, object]


def capture_defaults(
    session: SessionRecord,
    pending: PendingCapture,
    capture_id: str,
    requested_label: str,
    mode_registry: ModeRegistry | None = None,
) -> CaptureDefaults:
    """Return mode-specific save defaults without adding mode-specific handlers."""

    from metrology_process_planner.domains.session import built_in_mode_registry

    registry = mode_registry or built_in_mode_registry()
    definition = registry.definition(session.mode.value)
    sequence = _sequence_for_capture(session, capture_id)
    metadata = dict(pending.metadata or {})
    role = str(metadata.get("capture_role") or _role_for_mode(definition))
    capture_type = str(metadata.get("capture_type") or _type_for_mode(definition))
    label = requested_label or str(metadata.get("label") or _label(definition, sequence))
    metadata = _capture_metadata(definition, metadata, label, role, capture_type)
    return CaptureDefaults(sequence, label, role, capture_type, metadata)


def _label(definition: ModeDefinition, sequence: int) -> str:
    template = definition.capture.repeat_label_template or "Capture {sequence:03d}"
    try:
        return template.format(sequence=sequence)
    except (KeyError, ValueError):
        return f"Capture {sequence:03d}"


def _capture_metadata(
    definition: ModeDefinition,
    metadata: dict[str, object],
    label: str,
    role: str,
    capture_type: str,
) -> dict[str, object]:
    metadata["label"] = label
    metadata["capture_role"] = role
    metadata["capture_type"] = capture_type
    if definition.mode_id in {"cad_review", "cad_review_capture"}:
        metadata.setdefault("review_category", "layout_issue")
        metadata.setdefault("severity", "medium")
        metadata = normalized_cad_review_metadata(metadata)
    return metadata


def _role_for_mode(definition: ModeDefinition) -> str:
    roles = {
        "cad_review": "review_region",
        "cad_review_capture": "review_region",
        "optical_metrology": "optical_site",
        "cdsem_capture": "cdsem_site",
        "cdsem_measurement": "cdsem_site",
        "cdsem_planning": "cdsem_site",
        "grid_measurement": "grid_site",
    }
    return roles.get(definition.mode_id, definition.capture.site_role or "site")


def _type_for_mode(definition: ModeDefinition) -> str:
    types = {
        "cad_review": "cad_review_region",
        "cad_review_capture": "cad_review_region",
        "optical_metrology": "optical_metrology_site",
        "cdsem_capture": "cdsem_site",
        "cdsem_measurement": "cdsem_site",
        "cdsem_planning": "cdsem_site",
        "grid_measurement": "grid_measurement_site",
    }
    return types.get(definition.mode_id, definition.capture.saved_capture_type or "layout_region")


def _sequence_from_id(capture_id: str, fallback: int) -> int:
    suffix = capture_id.rsplit("-", 1)[-1]
    return int(suffix) if suffix.isdigit() else fallback


def _sequence_for_capture(session: SessionRecord, capture_id: str) -> int:
    generated = _sequence_from_id(capture_id, len(session.captures) + 1)
    previous = max((_capture_sequence(capture) for capture in session.captures), default=0)
    if generated <= previous:
        return previous + 1
    return generated


def _capture_sequence(capture: object) -> int:
    sequence = int(getattr(capture, "sequence", 0) or 0)
    if sequence > 0:
        return sequence
    return _sequence_from_id(str(getattr(capture, "id", "")), 0)

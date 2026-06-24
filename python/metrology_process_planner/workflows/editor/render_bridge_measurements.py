"""Measurement-owned render refresh operations."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from metrology_process_planner.domains.measurements import MeasurementRecord
from metrology_process_planner.domains.session import CaptureRecord, SessionRecord
from metrology_process_planner.domains.session.artifact_query import (
    artifact_refs_for_owner,
    first_display_artifact,
)
from metrology_process_planner.persistence.drawing_store import StoredDrawingExport
from metrology_process_planner.rendering import build_measurement_annotation_scene
from metrology_process_planner.rendering.scene import DrawingScene
from metrology_process_planner.workflows.editor.render_bridge_models import (
    RenderRefreshResult,
    RenderTarget,
)
from metrology_process_planner.workflows.editor.render_bridge_results import (
    _session_drawing_success,
    _warning,
    _with_warning,
)

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.render_bridge import SessionRenderBridge


def refresh_measurement_target(
    bridge: SessionRenderBridge,
    session: SessionRecord,
    target: RenderTarget,
) -> RenderRefreshResult:
    """Refresh one measurement-owned annotation target."""

    invalid = _invalid_measurement_target(session, target)
    if invalid is not None:
        return invalid
    capture, measurement = _measurement_owner(session, target.owner.owner_id)
    if capture is None or measurement is None:
        warning = _warning(
            target.owner,
            target.role,
            "missing-owner",
            f"Cannot refresh {target.role}; measurement {target.owner.owner_id} was not found.",
            severity="error",
        )
        return _with_warning(session, target.owner, target.role, warning, "error")
    try:
        scene = _build_measurement_scene(bridge, session, target, capture, measurement)
    except ValueError as exc:
        warning = _warning(target.owner, target.role, "validation", str(exc), severity="error")
        bridge.emit_render_failure("ArtifactRegenerationFailed", target.owner.owner_id, exc)
        return _with_warning(session, target.owner, target.role, warning, "error")
    try:
        stored = bridge.export_owner_scene("measurement", measurement.id, scene)
    except OSError as exc:
        warning = _warning(target.owner, target.role, "export", str(exc), severity="error")
        bridge.emit_render_failure("ArtifactExportFailed", target.owner.owner_id, exc)
        return _with_warning(session, target.owner, target.role, warning, "error")
    _emit_export_diagnostics(bridge, target, stored)
    result = _session_drawing_success(session, target.owner, target.role, stored)
    return replace(result, session=_with_measurement_artifacts(result.session, measurement.id))


def _build_measurement_scene(
    bridge: SessionRenderBridge,
    session: SessionRecord,
    target: RenderTarget,
    capture: CaptureRecord,
    measurement: MeasurementRecord,
) -> DrawingScene:
    bridge.emit_render_event(
        "ArtifactRegenerationStarted",
        target.owner.owner_id,
        target.role,
    )
    return build_measurement_annotation_scene(
        capture,
        measurement,
        first_display_artifact(session.artifacts or {}, "capture", capture.id),
    )


def _emit_export_diagnostics(
    bridge: SessionRenderBridge,
    target: RenderTarget,
    stored: StoredDrawingExport,
) -> None:
    for diagnostic in stored.export_result.diagnostics:
        bridge.emit_export_diagnostic(
            "ArtifactRasterizationWarning",
            target.owner.owner_id,
            target.role,
            diagnostic.message,
            diagnostic.exception_type,
            diagnostic.exception_message,
            diagnostic.stack_trace,
        )


def _invalid_measurement_target(
    session: SessionRecord,
    target: RenderTarget,
) -> RenderRefreshResult | None:
    if target.owner.owner_type != "measurement":
        return None
    if target.role == "measurement_annotation":
        return None
    warning = _warning(target.owner, target.role, "unsupported-role", "Unsupported role.")
    return _with_warning(session, target.owner, target.role, warning, "error")


def _measurement_owner(
    session: SessionRecord,
    measurement_id: str,
) -> tuple[CaptureRecord | None, MeasurementRecord | None]:
    for capture in session.captures:
        for measurement in capture.measurements:
            if measurement.id == measurement_id:
                return capture, measurement
    return None, None


def _with_measurement_artifacts(session: SessionRecord, measurement_id: str) -> SessionRecord:
    session = _without_placeholder(session, measurement_id)
    refs = artifact_refs_for_owner(session.artifacts or {}, "measurement", measurement_id)
    svg_ref = refs.get("measurement_annotation_svg")
    if svg_ref:
        refs = {**refs, "annotation": svg_ref}
    captures = tuple(
        _with_measurement_refs(capture, measurement_id, refs) for capture in session.captures
    )
    return replace(session, captures=captures)


def _with_measurement_refs(
    capture: CaptureRecord,
    measurement_id: str,
    refs: dict[str, str],
) -> CaptureRecord:
    measurements = tuple(
        replace(measurement, artifact_refs={**dict(measurement.artifact_refs or {}), **refs})
        if measurement.id == measurement_id
        else measurement
        for measurement in capture.measurements
    )
    return replace(capture, measurements=measurements)


def _without_placeholder(session: SessionRecord, measurement_id: str) -> SessionRecord:
    artifact_id = f"measurement-{measurement_id}-annotation"
    warning_id = f"warning-{artifact_id}-pending"
    artifacts = {
        key: value for key, value in dict(session.artifacts or {}).items() if key != artifact_id
    }
    captures = tuple(
        _clear_measurement_placeholder(capture, measurement_id) for capture in session.captures
    )
    warnings = tuple(warning for warning in session.warnings if warning.id != warning_id)
    return replace(session, artifacts=artifacts, captures=captures, warnings=warnings)


def _clear_measurement_placeholder(capture: CaptureRecord, measurement_id: str) -> CaptureRecord:
    measurements = tuple(
        _clear_placeholder_refs(measurement) if measurement.id == measurement_id else measurement
        for measurement in capture.measurements
    )
    return replace(capture, measurements=measurements)


def _clear_placeholder_refs(measurement: MeasurementRecord) -> MeasurementRecord:
    warning_id = f"warning-measurement-{measurement.id}-annotation-pending"
    refs = {
        role: artifact_id
        for role, artifact_id in dict(measurement.artifact_refs or {}).items()
        if artifact_id != f"measurement-{measurement.id}-annotation"
    }
    warnings = tuple(item for item in measurement.warning_ids if item != warning_id)
    return replace(measurement, artifact_refs=refs, warning_ids=warnings)

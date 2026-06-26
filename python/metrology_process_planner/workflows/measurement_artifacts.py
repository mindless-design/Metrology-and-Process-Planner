"""Repairable artifact registration for saved measurement records."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
    WarningRecord,
)


def ensure_measurement_artifacts(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> SessionRecord:
    """Ensure every saved measurement has a repairable detail artifact."""

    artifacts = dict(session.artifacts or {})
    warnings = {warning.id: warning for warning in session.warnings}
    captures = []
    for capture in session.captures:
        measurements = []
        for measurement in capture.measurements:
            if _has_visible_measurement_detail_artifact(
                session,
                measurement,
                artifacts,
                mode_registry,
            ):
                measurements.append(measurement)
                continue
            updated, artifact, warning = _measurement_artifact(measurement, capture.id)
            artifacts[artifact.id] = artifact
            warnings[warning.id] = warning
            measurements.append(updated)
        captures.append(replace(capture, measurements=tuple(measurements)))
    return replace(
        session,
        captures=tuple(captures),
        artifacts=artifacts,
        warnings=tuple(warnings.values()),
    )


def _has_visible_measurement_detail_artifact(
    session: SessionRecord,
    measurement: MeasurementRecord,
    artifacts: dict[str, ArtifactRecord],
    mode_registry: ModeRegistry | None,
) -> bool:
    artifact_id = str(dict(measurement.artifact_refs or {}).get("measurement_detail", ""))
    artifact = artifacts.get(artifact_id) if artifact_id else None
    return bool(
        artifact is not None
        and artifact_visible_for_session(session, artifact, mode_registry)
    )


def _measurement_artifact(
    measurement: MeasurementRecord,
    capture_id: str,
) -> tuple[MeasurementRecord, ArtifactRecord, WarningRecord]:
    artifact_id = f"measurement-{measurement.id}-annotation"
    warning_id = f"warning-{artifact_id}-pending"
    refs = {
        **dict(measurement.artifact_refs or {}),
        "annotation": artifact_id,
        "measurement_detail": artifact_id,
    }
    warning_ids = tuple(dict.fromkeys(measurement.warning_ids + (warning_id,)))
    updated = replace(measurement, artifact_refs=refs, warning_ids=warning_ids)
    artifact = ArtifactRecord(
        artifact_id,
        "measurement_detail",
        "Measurement Detail",
        f"drawings/measurements/{measurement.id}.svg",
        ArtifactOwnerRef("measurement", measurement.id, "measurement_detail"),
        status=ArtifactStatus.PENDING,
        generator="measurement_workflow",
        repair=ArtifactRepairMetadata("regenerate_artifact", "Generate measurement detail image."),
        warning_ids=(warning_id,),
        extensions={"capture_id": capture_id},
    )
    warning = WarningRecord(
        warning_id,
        "Measurement detail artifact has not been generated yet.",
        related_item_refs=(f"measurement:{measurement.id}",),
        related_artifact_refs=(artifact_id,),
        repair_suggestion="Regenerate the measurement detail artifact.",
    )
    return updated, artifact, warning

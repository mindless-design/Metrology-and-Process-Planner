"""Artifact invalidation rules for editable session records."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_invalidation_policy import (
    CAPTURE_LABEL_ROLES,
    EXPORT_RELEVANT_ROLES,
    EXPORT_RELEVANT_TYPES,
    MEASUREMENT_METADATA_ROLES,
)
from metrology_process_planner.domains.artifacts.artifact_registry import (
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.capture.captures import CaptureRecord
from metrology_process_planner.domains.modes.mode_registry import ModeRegistry
from metrology_process_planner.domains.session.process_outputs import ReportRecord
from metrology_process_planner.domains.session.record import SessionRecord


def invalidate_capture_edit(
    session: SessionRecord,
    capture_id: str,
    field_key: str,
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    """Mark capture-owned and derived artifacts stale after metadata changes."""

    return _invalidate(
        session,
        owner_type="capture",
        owner_id=capture_id,
        roles=tuple(sorted(CAPTURE_LABEL_ROLES)),
        reason=f"capture.{field_key} changed",
        export_relevant=True,
        mode_registry=mode_registry,
    )


def invalidate_measurement_edit(
    session: SessionRecord,
    measurement_id: str,
    field_key: str,
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    """Mark measurement-owned and derived artifacts stale after metadata changes."""

    return _invalidate(
        session,
        owner_type="measurement",
        owner_id=measurement_id,
        roles=tuple(sorted(MEASUREMENT_METADATA_ROLES)),
        reason=f"measurement.{field_key} changed",
        export_relevant=True,
        mode_registry=mode_registry,
    )


def invalidate_new_capture(
    session: SessionRecord,
    capture: CaptureRecord,
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    """Mark session-level exports stale after a capture is added."""

    return _invalidate(
        session,
        owner_type="capture",
        owner_id=capture.id,
        roles=(),
        reason=f"capture.{capture.id} added",
        export_relevant=True,
        mode_registry=mode_registry,
    )


def invalidate_exports(
    session: SessionRecord,
    reason: str,
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    """Mark session-level CSV and report outputs stale."""

    return _invalidate(
        session,
        owner_type="",
        owner_id="",
        roles=(),
        reason=reason,
        export_relevant=True,
        mode_registry=mode_registry,
    )


def _invalidate(
    session: SessionRecord,
    owner_type: str,
    owner_id: str,
    roles: tuple[str, ...],
    reason: str,
    export_relevant: bool,
    mode_registry: ModeRegistry | None,
) -> SessionRecord:
    artifacts = {
        artifact_id: _stale_if_needed(
            session,
            artifact,
            owner_type,
            owner_id,
            roles,
            reason,
            export_relevant,
            mode_registry,
        )
        for artifact_id, artifact in (session.artifacts or {}).items()
    }
    reports = _stale_reports(session.reports) if export_relevant else session.reports
    return replace(session, artifacts=artifacts, reports=reports)


def _stale_if_needed(
    session: SessionRecord,
    artifact: ArtifactRecord,
    owner_type: str,
    owner_id: str,
    roles: tuple[str, ...],
    reason: str,
    export_relevant: bool,
    mode_registry: ModeRegistry | None,
) -> ArtifactRecord:
    if artifact.status in {
        ArtifactStatus.MISSING,
        ArtifactStatus.FAILED,
        ArtifactStatus.PLACEHOLDER,
        ArtifactStatus.SUPERSEDED,
        ArtifactStatus.INTENTIONALLY_IGNORED,
    }:
        return artifact
    if not artifact_visible_for_session(session, artifact, mode_registry):
        return artifact
    if not _matches(artifact, owner_type, owner_id, roles, export_relevant):
        return artifact
    extensions = dict(artifact.extensions or {})
    extensions["stale_reason"] = reason
    return replace(artifact, status=ArtifactStatus.STALE, extensions=extensions)


def _matches(
    artifact: ArtifactRecord,
    owner_type: str,
    owner_id: str,
    roles: tuple[str, ...],
    export_relevant: bool,
) -> bool:
    if artifact.owner.owner_type == owner_type and artifact.owner.owner_id == owner_id:
        return not roles or artifact.owner.role in roles or artifact.type in roles
    if owner_type and owner_id and _depends_on(artifact, owner_type, owner_id):
        return True
    return export_relevant and _is_export_artifact(artifact)


def _depends_on(artifact: ArtifactRecord, owner_type: str, owner_id: str) -> bool:
    return any(
        dependency.kind == owner_type and dependency.id == owner_id
        for dependency in artifact.dependencies
    )


def _is_export_artifact(artifact: ArtifactRecord) -> bool:
    values = {
        artifact.type,
        artifact.owner.owner_type,
        artifact.owner.role,
        artifact.relative_path.rsplit(".", 1)[-1].lower(),
    }
    return bool(values & EXPORT_RELEVANT_TYPES or values & EXPORT_RELEVANT_ROLES)


def _stale_reports(reports: tuple[ReportRecord, ...]) -> tuple[ReportRecord, ...]:
    if not reports:
        return reports
    return tuple(
        replace(report, status="stale")
        if report.status not in {"missing", "failed", "placeholder", "superseded"}
        else report
        for report in reports
    )

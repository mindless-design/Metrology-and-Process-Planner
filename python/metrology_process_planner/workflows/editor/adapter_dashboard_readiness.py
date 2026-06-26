"""Recipe-free dashboard artifact readiness helpers."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ArtifactRecord, ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.warning_visibility import (
    editor_visible_warning_count,
)


def artifact_attention_count(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> int:
    """Return count of visible artifacts that need repair or review."""

    return sum(
        1
        for artifact in visible_dashboard_artifacts(session, mode_registry)
        if artifact.status.value in {
            "missing",
            "failed",
            "placeholder",
            "stale",
            "pending",
            "pending_solver",
        }
    )


def missing_artifact_count_for_dashboard(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> int:
    """Return count of visible artifacts that are strictly missing."""

    return sum(
        1
        for artifact in visible_dashboard_artifacts(session, mode_registry)
        if artifact.status.value == "missing"
    )


def report_readiness_for_dashboard(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> str:
    """Return compact report readiness text for recipe-free dashboard rows."""

    statuses = {
        artifact.status.value
        for artifact in _report_readiness_artifacts(session, mode_registry)
    }
    if "missing" in statuses:
        return "missing required artifacts"
    if "failed" in statuses:
        return "artifact repair required"
    if "pending" in statuses or "pending_solver" in statuses:
        return "artifact generation pending"
    if "stale" in statuses:
        return "stale outputs"
    if "placeholder" in statuses or editor_visible_warning_count(session, mode_registry) > 0:
        return "ready with warnings"
    return "ready"


def csv_readiness_for_dashboard(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> str:
    """Return compact CSV readiness text for recipe-free dashboard rows."""

    artifact = _csv_export_artifact(session, mode_registry)
    if artifact is None:
        return "not exported"
    if artifact.status.value == "present":
        return "ready"
    if artifact.status.value == "stale":
        return "stale"
    if artifact.status.value == "placeholder":
        return "placeholder"
    if artifact.status.value in {"missing", "failed"}:
        return "needs export"
    return artifact.status.value


def visible_dashboard_artifacts(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[ArtifactRecord, ...]:
    """Return artifacts visible to normal recipe-free editor dashboard state."""

    return tuple(
        artifact
        for artifact in (session.artifacts or {}).values()
        if artifact_visible_for_session(session, artifact, mode_registry)
    )


def _report_readiness_artifacts(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[ArtifactRecord, ...]:
    return tuple(
        artifact
        for artifact in visible_dashboard_artifacts(session, mode_registry)
        if not _is_csv_export_artifact(artifact)
    )


def _csv_export_artifact(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> ArtifactRecord | None:
    for artifact in visible_dashboard_artifacts(session, mode_registry):
        if _is_csv_export_artifact(artifact):
            return artifact
    return None


def _is_csv_export_artifact(artifact: ArtifactRecord) -> bool:
    return artifact.owner.owner_type == "session" and (
        artifact.owner.role == "csv_export" or artifact.type == "csv_export"
    )

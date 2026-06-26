"""Helper functions for artifact repair service."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.workflows.artifacts.requests import (
    RepairRequest,
    RepairRequestStatus,
    RepairType,
)
from metrology_process_planner.workflows.artifacts.warnings import (
    ARTIFACT_REGENERATION_FAILED,
    ARTIFACT_REPAIR_UNAVAILABLE,
    PARENT_IMAGE_REQUIRED_FOR_REPAIR,
    RECIPE_REQUIRED_FOR_REPAIR,
    SOLVER_REQUIRED_FOR_REPAIR,
    SOURCE_LAYOUT_REQUIRED_FOR_REPAIR,
    artifact_warning,
    upsert_warning,
)


def repair_request_for(session: SessionRecord, artifact: ArtifactRecord) -> RepairRequest:
    """Build one artifact repair request."""

    requirements = _requirements(session, artifact)
    repair_type = _repair_type(artifact)
    status = (
        RepairRequestStatus.AVAILABLE
        if artifact.repair.regenerable and not requirements
        else RepairRequestStatus.UNAVAILABLE
    )
    owner = artifact.owner
    return RepairRequest(
        repair_id=f"repair-{artifact.id}-{repair_type.value}",
        artifact_id=artifact.id,
        repair_type=repair_type,
        owner_ref=f"{owner.owner_type}:{owner.owner_id}:{owner.role}",
        requirements=requirements,
        status=status,
        user_message=_request_message(artifact, requirements, status),
        technical_details="; ".join(requirements),
    )


def is_process_only_repair_artifact(
    session: SessionRecord,
    artifact: ArtifactRecord,
    mode_registry: ModeRegistry | None = None,
) -> bool:
    """Return whether a repair task should be hidden outside process-aware modes."""

    return not artifact_visible_for_session(session, artifact, mode_registry)


def with_unavailable(
    session: SessionRecord,
    artifact: ArtifactRecord,
    request: RepairRequest,
) -> SessionRecord:
    """Return a session with an unavailable-repair warning."""

    code = request.requirements[0] if request.requirements else ARTIFACT_REPAIR_UNAVAILABLE
    warning = artifact_warning(
        artifact,
        code,
        request.user_message,
        request.technical_details,
        "Restore the required context or relink a replacement artifact.",
    )
    warnings = {item.id: item for item in session.warnings}
    stored = upsert_warning(warnings, warning)
    artifacts = dict(session.artifacts or {})
    artifacts[artifact.id] = replace(
        artifact,
        warning_ids=tuple(sorted(set(artifact.warning_ids + (stored.id,)))),
    )
    return replace(session, artifacts=artifacts, warnings=tuple(warnings.values()))


def with_failed_generation(
    session: SessionRecord,
    artifact: ArtifactRecord,
    error: str,
) -> SessionRecord:
    """Return a session with failed-generation artifact state."""

    warning = artifact_warning(
        artifact,
        ARTIFACT_REGENERATION_FAILED,
        f"Artifact regeneration failed: {artifact.label or artifact.id}",
        error,
        "Review generator diagnostics and retry.",
        severity="error",
    )
    warnings = {item.id: item for item in session.warnings}
    stored = upsert_warning(warnings, warning)
    failed = replace(
        artifact,
        status=ArtifactStatus.FAILED,
        repair=replace(artifact.repair, last_error=error),
        warning_ids=tuple(sorted(set(artifact.warning_ids + (stored.id,)))),
    )
    artifacts = dict(session.artifacts or {})
    artifacts[artifact.id] = failed
    return replace(session, artifacts=artifacts, warnings=tuple(warnings.values()))


def mark_artifact_ignored(
    artifact: ArtifactRecord,
    warning_id_value: str,
) -> ArtifactRecord:
    """Return an artifact marked ignored when it owns the warning id."""

    if warning_id_value not in artifact.warning_ids:
        return artifact
    return replace(artifact, status=ArtifactStatus.INTENTIONALLY_IGNORED)


def _requirements(session: SessionRecord, artifact: ArtifactRecord) -> tuple[str, ...]:
    requirements: list[str] = []
    repair = artifact.repair
    if repair.requires_live_layout and not session.source_layout.layout_path:
        requirements.append(SOURCE_LAYOUT_REQUIRED_FOR_REPAIR)
    if repair.requires_recipe and not session.process_context.recipe_path:
        requirements.append(RECIPE_REQUIRED_FOR_REPAIR)
    if repair.requires_solver and not session.process_context.solver_backend:
        requirements.append(SOLVER_REQUIRED_FOR_REPAIR)
    if repair.requires_parent_image and _parent_image_missing(session, artifact):
        requirements.append(PARENT_IMAGE_REQUIRED_FOR_REPAIR)
    return tuple(requirements)


def _parent_image_missing(session: SessionRecord, artifact: ArtifactRecord) -> bool:
    parent_id = artifact.owner.owner_id
    for dependency in artifact.dependencies:
        if dependency.artifact_id:
            parent = (session.artifacts or {}).get(dependency.artifact_id)
            return parent is None or parent.status is not ArtifactStatus.PRESENT
    return not any(
        item.owner.owner_type == "capture"
        and item.owner.owner_id == parent_id
        and item.status is ArtifactStatus.PRESENT
        for item in (session.artifacts or {}).values()
    )


def _repair_type(artifact: ArtifactRecord) -> RepairType:
    if _is_report_artifact(artifact):
        return RepairType.REBUILD_REPORT
    if artifact.type == "csv_export":
        return RepairType.REBUILD_CSV
    if artifact.type in _REPORT_ARTIFACT_TYPES:
        return RepairType.REBUILD_REPORT
    return RepairType.REGENERATE_ARTIFACT


def _is_report_artifact(artifact: ArtifactRecord) -> bool:
    return artifact.owner.owner_type == "report"


def _request_message(
    artifact: ArtifactRecord,
    requirements: tuple[str, ...],
    status: RepairRequestStatus,
) -> str:
    if artifact.repair.requires_live_layout and SOURCE_LAYOUT_REQUIRED_FOR_REPAIR in requirements:
        return "Reopen the source layout before regenerating this artifact."
    if requirements:
        return "Artifact repair is blocked by missing context."
    if status is RepairRequestStatus.AVAILABLE:
        return "Artifact can be regenerated."
    return "No generator is available for this artifact."


_REPORT_ARTIFACT_TYPES = {
    "powerpoint_deck",
    "powerpoint_export",
    "pdf_report",
    "image_bundle",
    "report",
    "report_manifest",
}

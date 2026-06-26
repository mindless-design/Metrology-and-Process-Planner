"""Helper operations for artifact repair service decisions."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.workflows.artifacts.generators import ArtifactGeneratorRegistry
from metrology_process_planner.workflows.artifacts.repair_requirements import (
    with_registration_requirements,
)
from metrology_process_planner.workflows.artifacts.repair_support import (
    is_process_only_repair_artifact,
    mark_artifact_ignored,
    repair_request_for,
)
from metrology_process_planner.workflows.artifacts.requests import (
    RepairRequest,
    RepairRequestStatus,
)


def repair_candidate_artifacts(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[ArtifactRecord, ...]:
    """Return artifacts with actionable repair lifecycle statuses."""

    statuses = {
        ArtifactStatus.MISSING,
        ArtifactStatus.STALE,
        ArtifactStatus.FAILED,
        ArtifactStatus.PLACEHOLDER,
    }
    return tuple(
        artifact
        for artifact in (session.artifacts or {}).values()
        if artifact.status in statuses
        and not is_process_only_repair_artifact(session, artifact, mode_registry)
    )


def repair_request_with_generator(
    session: SessionRecord,
    artifact: ArtifactRecord,
    generators: ArtifactGeneratorRegistry,
) -> RepairRequest:
    """Return a repair request after applying generator availability checks."""

    request = repair_request_for(session, artifact)
    if request.status is not RepairRequestStatus.AVAILABLE:
        return request
    registration = generators.generator_for(artifact)
    requirement_request = with_registration_requirements(session, request, registration)
    if requirement_request.status is not RepairRequestStatus.AVAILABLE:
        return requirement_request
    if registration is not None and registration.handler is not None:
        return request
    return replace(
        request,
        status=RepairRequestStatus.UNAVAILABLE,
        requirements=request.requirements + ("GENERATOR_HANDLER_UNAVAILABLE",),
        user_message="No generator handler is registered for this artifact.",
        technical_details="GENERATOR_HANDLER_UNAVAILABLE",
    )


def with_ignored_warning(session: SessionRecord, warning_id_value: str) -> SessionRecord:
    """Return a session with one artifact warning intentionally ignored."""

    warnings = tuple(
        replace(warning, status="ignored")
        if warning.id == warning_id_value
        else warning
        for warning in session.warnings
    )
    artifacts = {
        artifact_id: mark_artifact_ignored(artifact, warning_id_value)
        for artifact_id, artifact in (session.artifacts or {}).items()
    }
    return replace(session, artifacts=artifacts, warnings=warnings)

"""Regenerate existing capture-owned visual artifact records."""

from __future__ import annotations

from metrology_process_planner.domains.session import ArtifactRecord, CaptureRecord, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.generators import ArtifactGenerationResult
from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
    generate_annotation_artifact,
    generate_labeled_site_artifact,
    generate_site_overview_artifact,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    artifact_by_owner_role as _artifact_by_owner_role,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    capture_by_id as _capture_by_id,
)

_OVERVIEW_ROLES = {
    "site_overview_image",
    "site_overview_labeled",
    "site_overview_context",
}
_ANNOTATION_ROLES = {
    "line_annotation_image",
    "point_annotation_image",
    "measurement_annotation_image",
    "line_annotation",
    "point_annotation",
}


def regenerate_capture_visual_artifact(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
) -> ArtifactGenerationResult:
    """Regenerate one capture visual polish artifact."""

    capture = _capture_by_id(session, artifact.owner.owner_id)
    if capture is None:
        raise RuntimeError(f"Capture {artifact.owner.owner_id} was not found.")
    role = artifact.owner.role or artifact.type
    updated = _regenerate_visual_role(session, capture, paths, role, artifact.id)
    return ArtifactGenerationResult(
        _generated_artifact(updated, artifact.id, capture.id, role),
        updated,
    )


def _regenerate_visual_role(
    session: SessionRecord,
    capture: CaptureRecord,
    paths: SessionPaths,
    role: str,
    artifact_id: str,
) -> SessionRecord:
    if role == "site_image_labeled":
        return generate_labeled_site_artifact(session, capture, paths)
    if role in _OVERVIEW_ROLES:
        return generate_site_overview_artifact(session, capture, paths, role)
    if role in _ANNOTATION_ROLES:
        return generate_annotation_artifact(session, capture, paths, role)
    raise RuntimeError(f"Artifact {artifact_id} is not a capture visual artifact.")


def _generated_artifact(
    session: SessionRecord,
    artifact_id: str,
    capture_id: str,
    role: str,
) -> ArtifactRecord:
    generated = dict(session.artifacts or {}).get(artifact_id)
    if generated is not None:
        return generated
    generated = _artifact_by_owner_role(session, "capture", capture_id, role)
    if generated is None:
        raise RuntimeError(f"Generator did not produce artifact {artifact_id}.")
    return generated

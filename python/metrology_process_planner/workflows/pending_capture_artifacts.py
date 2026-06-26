"""Artifact promotion helpers for saved pending captures."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    CaptureRecord,
    PendingCapture,
    WarningRecord,
)
from metrology_process_planner.workflows.artifacts.placeholders import placeholder_artifact
from metrology_process_planner.workflows.artifacts.warnings import (
    ARTIFACT_MISSING,
    artifact_warning,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import (
    pending_capture_artifact,
)


def capture_with_promoted_artifacts(
    pending: PendingCapture,
    capture: CaptureRecord,
    capture_id: str,
    artifacts: dict[str, ArtifactRecord],
    warnings: dict[str, WarningRecord],
) -> CaptureRecord:
    """Promote pending artifacts or create visible placeholders for saved capture output."""

    refs = dict(capture.artifact_refs or {})
    warning_ids = list(capture.warning_ids)
    for role, artifact in (
        ("crop", pending_capture_artifact(pending, capture_id)),
        ("site_image", _site_image_artifact(pending, capture_id, warnings)),
    ):
        if artifact is not None:
            artifacts[artifact.id] = artifact
            refs[role] = artifact.id
            warning_ids.extend(artifact.warning_ids)
    return replace(capture, artifact_refs=refs, warning_ids=tuple(dict.fromkeys(warning_ids)))


def _site_image_artifact(
    pending: PendingCapture,
    capture_id: str,
    warnings: dict[str, WarningRecord],
) -> ArtifactRecord | None:
    from metrology_process_planner.workflows.canvas_interaction_helpers import (
        _pending_capture_site_image_artifact,
    )

    artifact = _pending_capture_site_image_artifact(pending, capture_id)
    if artifact is not None:
        return artifact
    placeholder = _missing_site_image_placeholder(capture_id)
    warning = artifact_warning(
        placeholder,
        ARTIFACT_MISSING,
        "Capture site image is missing.",
        "The capture was saved without an image artifact path.",
        "Regenerate the site image from the current layout view.",
    )
    warnings[warning.id] = warning
    return replace(placeholder, warning_ids=(warning.id,))


def _missing_site_image_placeholder(capture_id: str) -> ArtifactRecord:
    artifact = ArtifactRecord(
        artifact_id("capture", capture_id, "site_image"),
        "placeholder",
        "site_image",
        f"artifacts/placeholders/{capture_id}-site_image.svg",
        ArtifactOwnerRef("capture", capture_id, "site_image"),
        status=ArtifactStatus.MISSING,
        file=ArtifactFileMetadata(content_type="image/svg+xml"),
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_artifact",
            repair_suggestion="Regenerate the site image from the current layout view.",
            regenerable=True,
            requires_live_layout=True,
        ),
    )
    return placeholder_artifact(
        artifact,
        "The capture was saved without an image artifact path.",
        "Regenerate the site image from the current layout view.",
        "CSV export can continue; reports may use this placeholder.",
    )

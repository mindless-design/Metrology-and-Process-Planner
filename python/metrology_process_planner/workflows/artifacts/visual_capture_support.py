"""Support helpers for capture-owned visual artifact generation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import PurePosixPath

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.artifacts.artifact_query import artifact_for_role
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    CaptureRecord,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.rendering.visual_labels import LabelSpec


def artifact_record(
    capture: CaptureRecord,
    role: str,
    artifact_type: str,
    relative_path: str,
    label: LabelSpec,
) -> ArtifactRecord:
    """Return a present capture-owned visual artifact record."""

    return ArtifactRecord(
        artifact_id("capture", capture.id, role),
        artifact_type,
        role.replace("_", " ").title(),
        relative_path,
        ArtifactOwnerRef("capture", capture.id, role),
        status=ArtifactStatus.PRESENT,
        generator="visual_capture_polish",
        file=ArtifactFileMetadata(width_px=1024, height_px=768, content_type="image/svg+xml"),
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_artifact",
            repair_suggestion="Regenerate the visual artifact.",
            regenerable=True,
        ),
        extensions={
            "style_profile_id": "engineering_dark",
            "theme_id": "engineering_dark",
            "label_policy_id": "site_label_standard",
            "label_spec": label.to_dict(),
        },
    )


def with_capture_artifact(
    session: SessionRecord,
    capture_id: str,
    artifact: ArtifactRecord,
    warnings: tuple[WarningRecord, ...],
) -> SessionRecord:
    """Return a session updated with one capture visual artifact."""

    artifacts = {**dict(session.artifacts or {}), artifact.id: artifact}
    warning_ids = {warning.id for warning in warnings}
    captures = tuple(
        _capture_with_artifact(capture, capture_id, artifact, warning_ids)
        for capture in session.captures
    )
    session_warnings = _replace_warnings(session.warnings, warnings)
    return replace(session, artifacts=artifacts, captures=captures, warnings=session_warnings)


def raw_site_artifact(session: SessionRecord, capture: CaptureRecord) -> ArtifactRecord | None:
    """Return the preferred raw image artifact for a capture."""

    artifacts = tuple(
        artifact
        for artifact in (session.artifacts or {}).values()
        if artifact.owner.owner_type == "capture" and artifact.owner.owner_id == capture.id
    )
    return artifact_for_role(artifacts, "site_image") or artifact_for_role(artifacts, "crop")


def annotation_role(capture: CaptureRecord) -> str:
    """Return the default annotation role for a capture."""

    for feature in capture.geometry.features:
        kind = str(feature.get("kind", feature.get("type", "")))
        if "point" in kind or "ellipsometry" in kind:
            return "point_annotation_image"
    return "line_annotation_image" if capture.geometry.features else "measurement_annotation_image"


def normalized_annotation_role(role: str) -> str:
    """Return the canonical image role for an annotation request."""

    if role == "line_annotation":
        return "line_annotation_image"
    if role == "point_annotation":
        return "point_annotation_image"
    return role


def capture_by_id(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    """Return a capture by id."""

    return next((capture for capture in session.captures if capture.id == capture_id), None)


def artifact_by_owner_role(
    session: SessionRecord,
    owner_type: str,
    owner_id: str,
    role: str,
) -> ArtifactRecord | None:
    """Return an artifact by owner and role."""

    return next(
        (
            artifact
            for artifact in (session.artifacts or {}).values()
            if artifact.owner.owner_type == owner_type
            and artifact.owner.owner_id == owner_id
            and artifact.owner.role == role
        ),
        None,
    )


def warning(artifact: ArtifactRecord, code: str, message: str = "") -> WarningRecord:
    """Return a visual artifact repair warning."""

    return WarningRecord(
        id=f"warning-{artifact.id}-{code.lower()}",
        code=code,
        source="visual_capture_polish",
        severity="warning",
        message=message or code.replace("_", " ").title(),
        related_item_refs=(f"capture:{artifact.owner.owner_id}",),
        related_artifact_refs=(artifact.id,),
        artifact_path=artifact.relative_path,
        repair_suggestion="Regenerate the visual artifact.",
    )


def svg_path(capture_id: str, role: str) -> str:
    """Return the default relative SVG path for a capture visual artifact."""

    return f"images/{_safe(capture_id)}-{role}.svg"


def relative_href(source_relative_path: str, target_relative_path: str) -> str:
    """Return an SVG href from one artifact path to another artifact path."""

    source_parent = PurePosixPath(source_relative_path).parent
    target = PurePosixPath(target_relative_path)
    if str(source_parent) in {"", "."}:
        return target.as_posix()
    try:
        return target.relative_to(source_parent).as_posix()
    except ValueError:
        parts = [part for part in source_parent.parts if part not in {"", "."}]
        return (PurePosixPath(*(".." for _ in parts)) / target).as_posix()


def write_text_artifact(paths: SessionPaths, relative_path: str, text: str) -> None:
    """Write a text artifact to the session artifact folder."""

    destination = artifact_path_to_disk(paths.folder, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def _capture_with_artifact(
    capture: CaptureRecord,
    capture_id: str,
    artifact: ArtifactRecord,
    warning_ids: set[str],
) -> CaptureRecord:
    if capture.id != capture_id:
        return capture
    artifact_refs = {**dict(capture.artifact_refs or {}), artifact.owner.role: artifact.id}
    if not warning_ids:
        return replace(capture, artifact_refs=artifact_refs)
    return replace(
        capture,
        artifact_refs=artifact_refs,
        warning_ids=tuple(dict.fromkeys(capture.warning_ids + tuple(warning_ids))),
    )


def _replace_warnings(
    current: tuple[WarningRecord, ...],
    warnings: tuple[WarningRecord, ...],
) -> tuple[WarningRecord, ...]:
    warning_ids = {warning.id for warning in warnings}
    return tuple(warning for warning in current if warning.id not in warning_ids) + warnings


def _safe(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value).strip("-")

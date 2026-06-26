"""Artifact columns for capture summary CSV exports."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from metrology_process_planner.domains.artifacts.artifact_query import (
    artifact_for_role,
    artifacts_for_owner,
)
from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord


def artifact_columns(
    session: SessionRecord,
    capture_id: str,
    measurements: Iterable[Any] = (),
    mode_registry: ModeRegistry | None = None,
) -> dict[str, str]:
    """Return artifact path and status columns for one capture."""

    capture_artifacts = tuple(
        artifact
        for artifact in artifacts_for_owner(session.artifacts or {}, "capture", capture_id)
        if artifact_visible_for_session(session, artifact, mode_registry)
    )
    measurement_artifacts = _visible_measurement_artifacts(session, measurements, mode_registry)
    artifacts = capture_artifacts + measurement_artifacts
    site_image = artifact_for_role(capture_artifacts, "site_image") or artifact_for_role(
        capture_artifacts,
        "crop",
    )
    annotation = _annotation_artifact(capture_artifacts)
    measurement_artifact = artifact_for_role(
        capture_artifacts,
        "measurement_annotation_png",
    ) or artifact_for_role(capture_artifacts, "measurement_annotation_svg")
    return {
        "site_image_artifact_id": _artifact_value(site_image, "id"),
        "site_image_path": _artifact_value(site_image, "relative_path"),
        "site_image_status": _status_value(site_image),
        "annotation_artifact_id": _artifact_value(annotation, "id"),
        "annotation_artifact_path": _artifact_value(annotation, "relative_path"),
        "annotation_artifact_status": _status_value(annotation),
        "measurement_artifact_id": _artifact_value(measurement_artifact, "id"),
        "measurement_artifact_path": _artifact_value(measurement_artifact, "relative_path"),
        "measurement_artifact_status": _status_value(measurement_artifact),
        "image_paths": _join(
            artifact.relative_path for artifact in artifacts if _include_path_in_summary(artifact)
        ),
        "artifact_statuses": _join(
            f"{artifact.owner.role}:{artifact.status.value}" for artifact in artifacts
        ),
    }


def measurement_artifact_columns(
    session: SessionRecord,
    measurement: Any,
    mode_registry: ModeRegistry | None = None,
) -> dict[str, str]:
    """Return artifact columns for a measurement-owned detail artifact."""

    if measurement is None:
        return {}
    artifact = _visible_measurement_artifact(session, measurement, mode_registry)
    if artifact is None:
        return {}
    return {
        "measurement_artifact_id": artifact.id,
        "measurement_artifact_path": artifact.relative_path,
        "measurement_artifact_status": artifact.status.value,
    }


def _visible_measurement_artifacts(
    session: SessionRecord,
    measurements: Iterable[Any],
    mode_registry: ModeRegistry | None,
) -> tuple[Any, ...]:
    artifacts = []
    seen: set[str] = set()
    for measurement in measurements:
        artifact = _visible_measurement_artifact(session, measurement, mode_registry)
        if artifact is not None and artifact.id not in seen:
            artifacts.append(artifact)
            seen.add(artifact.id)
    return tuple(artifacts)


def _visible_measurement_artifact(
    session: SessionRecord,
    measurement: Any,
    mode_registry: ModeRegistry | None,
) -> Any:
    artifacts = session.artifacts or {}
    refs = dict(measurement.artifact_refs or {})
    for role in ("measurement_detail", "annotation"):
        artifact_id = refs.get(role)
        artifact = artifacts.get(str(artifact_id)) if artifact_id else None
        if artifact is not None and artifact_visible_for_session(session, artifact, mode_registry):
            return artifact
    return None


def _join(values: Iterable[object]) -> str:
    return ";".join(str(value) for value in values)


def _artifact_value(artifact: Any, attribute: str) -> str:
    return "" if artifact is None else str(getattr(artifact, attribute))


def _status_value(artifact: Any) -> str:
    return "" if artifact is None else str(artifact.status.value)


def _include_path_in_summary(artifact: Any) -> bool:
    return artifact.type in {"image", "svg", "measurement_detail", "measurement_detail_image"}


def _annotation_artifact(artifacts: tuple[Any, ...]) -> Any:
    for role in (
        "line_annotation_png",
        "point_annotation_png",
        "layout_annotation_png",
        "review_annotation_png",
        "line_annotation",
        "point_annotation",
        "layout_annotation",
        "review_annotation",
        "line_annotation_svg",
        "point_annotation_svg",
        "layout_annotation_svg",
        "review_annotation_svg",
    ):
        artifact = artifact_for_role(artifacts, role)
        if artifact is not None:
            return artifact
    return None

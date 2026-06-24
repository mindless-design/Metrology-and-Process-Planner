"""Migration-only artifact parsing for integer-schema session payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metrology_process_planner.domains.session.artifact_content import artifact_content_type
from metrology_process_planner.domains.session.artifact_ids import artifact_id
from metrology_process_planner.domains.session.artifact_registry import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
)


def legacy_artifacts(data: Mapping[str, Any]) -> dict[str, ArtifactRecord]:
    """Return canonical registry records parsed from old embedded artifact fields."""

    artifacts: dict[str, ArtifactRecord] = {}
    for capture_data in _mapping_items(data.get("captures")):
        capture_id = str(capture_data.get("id", ""))
        artifacts.update(_capture_artifacts(capture_id, capture_data))
    for pending_data in _mapping_items(data.get("pending_captures")):
        artifact = _pending_artifact(pending_data)
        if artifact is not None:
            artifacts[artifact.id] = artifact
    for drawing_data in _mapping_items(data.get("drawings")):
        for artifact in _drawing_artifacts_from_owner(drawing_data):
            artifacts[artifact.id] = artifact
    for export_data in _mapping_items(data.get("exports")):
        artifact = _export_artifact(export_data)
        if artifact is not None:
            artifacts[artifact.id] = artifact
    return artifacts


def _capture_artifacts(
    capture_id: str,
    capture_data: Mapping[str, Any],
) -> dict[str, ArtifactRecord]:
    artifacts: dict[str, ArtifactRecord] = {}
    for image_data in _mapping_items(capture_data.get("images")):
        artifact = _image_artifact("capture", capture_id, image_data)
        if artifact is not None:
            artifacts[artifact.id] = artifact
    for drawing_data in _mapping_items(capture_data.get("drawings")):
        for artifact in _drawing_artifacts("capture", capture_id, drawing_data):
            artifacts[artifact.id] = artifact
    return artifacts


def _pending_artifact(data: Mapping[str, Any]) -> ArtifactRecord | None:
    path = data.get("image_artifact_path")
    if not path:
        return None
    return _artifact(
        owner_type="pending_capture",
        owner_id=str(data.get("id", "")),
        role="pending_crop",
        artifact_type="image",
        label="pending_crop",
        relative_path=str(path),
        status=ArtifactStatus.PENDING,
    )


def _drawing_artifacts_from_owner(data: Mapping[str, Any]) -> tuple[ArtifactRecord, ...]:
    return _drawing_artifacts(
        str(data.get("owner_type", "")),
        str(data.get("owner_id", "")),
        data,
    )


def _drawing_artifacts(
    owner_type: str,
    owner_id: str,
    data: Mapping[str, Any],
) -> tuple[ArtifactRecord, ...]:
    role = str(data.get("role", "drawing"))
    records = [
        _drawing_part(owner_type, owner_id, role, "spec", str(data.get("spec_path", "")), data),
        _drawing_part(owner_type, owner_id, role, "svg", str(data.get("svg_path", "")), data),
    ]
    png_path = data.get("png_path")
    if png_path:
        records.append(_drawing_part(owner_type, owner_id, role, "png", str(png_path), data))
    return tuple(record for record in records if record is not None)


def _drawing_part(
    owner_type: str,
    owner_id: str,
    role: str,
    part: str,
    path: str,
    data: Mapping[str, Any],
) -> ArtifactRecord | None:
    if not path:
        return None
    artifact_type = "drawing_spec" if part == "spec" else ("svg" if part == "svg" else "image")
    width = _optional_int(data.get("width_px")) if part != "spec" else None
    height = _optional_int(data.get("height_px")) if part != "spec" else None
    return _artifact(
        owner_type=owner_type,
        owner_id=owner_id,
        role=f"{role}_{part}",
        artifact_type=artifact_type,
        label=f"{role} {part.upper()}",
        relative_path=path,
        file=ArtifactFileMetadata(
            sha256=_optional_str(data.get("sha256")),
            width_px=width,
            height_px=height,
            content_type=artifact_content_type(path),
        ),
        trace_ids=_mapping(data.get("trace_ids")),
    )


def _image_artifact(
    owner_type: str,
    owner_id: str,
    data: Mapping[str, Any],
) -> ArtifactRecord | None:
    path = data.get("path")
    if not path:
        return None
    role = str(data.get("role", "image"))
    return _artifact(
        owner_type=owner_type,
        owner_id=owner_id,
        role=role,
        artifact_type="image",
        label=role,
        relative_path=str(path),
        file=ArtifactFileMetadata(
            sha256=_optional_str(data.get("sha256")),
            width_px=_optional_int(data.get("width_px")),
            height_px=_optional_int(data.get("height_px")),
            content_type=artifact_content_type(str(path)),
        ),
        trace_ids=_mapping(data.get("trace_ids")),
    )


def _export_artifact(data: Mapping[str, Any]) -> ArtifactRecord | None:
    export_id = data.get("id")
    path = data.get("path")
    if not export_id or not path:
        return None
    role = str(data.get("kind", "export"))
    return _artifact(
        owner_type="report",
        owner_id=str(export_id),
        role=role,
        artifact_type=role,
        label=role,
        relative_path=str(path),
    )


def _artifact(
    *,
    owner_type: str,
    owner_id: str,
    role: str,
    artifact_type: str,
    label: str,
    relative_path: str,
    status: ArtifactStatus = ArtifactStatus.PRESENT,
    file: ArtifactFileMetadata | None = None,
    trace_ids: Mapping[str, str] | None = None,
) -> ArtifactRecord:
    return ArtifactRecord(
        id=artifact_id(owner_type, owner_id, role),
        type=artifact_type,
        label=label,
        relative_path=relative_path,
        owner=ArtifactOwnerRef(owner_type, owner_id, role),
        status=status,
        file=file
        if file is not None
        else ArtifactFileMetadata(content_type=artifact_content_type(relative_path)),
        trace_ids=trace_ids or {},
    )


def _mapping_items(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _mapping(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)

"""Persistence helpers for editable drawing scene artifacts."""

from __future__ import annotations

from dataclasses import dataclass, replace

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    CaptureRecord,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.persistence.artifact_ref_sync import visible_artifact_refs_for_owner
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.rendering.export import (
    DrawingExporter,
    DrawingExportResult,
    SvgRasterizer,
)
from metrology_process_planner.rendering.scene import DrawingScene


@dataclass(frozen=True)
class StoredDrawingExport:
    """Canonical export result produced after storing a drawing scene."""

    owner_type: str
    owner_id: str
    role: str
    artifacts: tuple[ArtifactRecord, ...]
    export_result: DrawingExportResult

    @property
    def paths(self) -> tuple[str, ...]:
        """Return generated artifact paths in write order."""

        return tuple(artifact.relative_path for artifact in self.artifacts)


class SessionDrawingStore:
    """Write drawing specs and generated outputs into a session folder."""

    def __init__(self, exporter: DrawingExporter | None = None) -> None:
        self._exporter = exporter if exporter is not None else DrawingExporter()

    def export_capture_scene(
        self,
        paths: SessionPaths,
        capture_id: str,
        scene: DrawingScene,
        rasterizer: SvgRasterizer | None = None,
    ) -> StoredDrawingExport:
        """Export one capture drawing scene and return canonical metadata."""

        return self.export_owner_scene(paths, "capture", capture_id, scene, rasterizer)

    def export_owner_scene(
        self,
        paths: SessionPaths,
        owner_type: str,
        owner_id: str,
        scene: DrawingScene,
        rasterizer: SvgRasterizer | None = None,
    ) -> StoredDrawingExport:
        """Export one owner drawing scene and return canonical artifact metadata."""

        paths.ensure_created()
        stem = _safe_stem(
            owner_id if owner_type == "capture" else f"{owner_type}-{owner_id}",
            scene.role,
        )
        spec_path = f"drawings/{stem}.json"
        svg_path = f"images/{stem}.svg"
        png_path = f"images/{stem}.png"
        result = self._exporter.export(
            scene,
            artifact_path_to_disk(paths.folder, spec_path),
            artifact_path_to_disk(paths.folder, svg_path),
            artifact_path_to_disk(paths.folder, png_path),
            rasterizer,
        )
        return StoredDrawingExport(
            owner_type=owner_type,
            owner_id=owner_id,
            role=scene.role,
            artifacts=_drawing_artifacts(
                owner_type,
                owner_id,
                scene.role,
                spec_path,
                svg_path,
                png_path if result.png_path is not None else None,
                result.width_px,
                result.height_px,
            ),
            export_result=result,
        )


def upsert_drawing_artifacts(
    session: SessionRecord,
    stored: StoredDrawingExport,
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    """Return a session with one owner/role drawing artifact set replaced."""

    artifacts = _without_owner_role_artifacts(session, stored)
    artifacts.update({artifact.id: artifact for artifact in stored.artifacts})
    captures = _captures_with_refs(session, stored, artifacts, mode_registry)
    return replace(session, artifacts=artifacts, captures=captures)


def _without_owner_role_artifacts(
    session: SessionRecord,
    stored: StoredDrawingExport,
) -> dict[str, ArtifactRecord]:
    owner_role_prefix = f"{stored.role}_"
    return {
        key: artifact
        for key, artifact in dict(session.artifacts or {}).items()
        if not _matches_owner_role(artifact, stored, owner_role_prefix)
    }


def _matches_owner_role(
    artifact: ArtifactRecord,
    stored: StoredDrawingExport,
    owner_role_prefix: str,
) -> bool:
    return (
        artifact.owner.owner_type == stored.owner_type
        and artifact.owner.owner_id == stored.owner_id
        and artifact.owner.role.startswith(owner_role_prefix)
    )


def _captures_with_refs(
    session: SessionRecord,
    stored: StoredDrawingExport,
    artifacts: dict[str, ArtifactRecord],
    mode_registry: ModeRegistry | None,
) -> tuple[CaptureRecord, ...]:
    if stored.owner_type != "capture":
        return session.captures
    refs = visible_artifact_refs_for_owner(
        session,
        artifacts,
        "capture",
        stored.owner_id,
        mode_registry,
    )
    return tuple(
        replace(capture, artifact_refs={**dict(capture.artifact_refs or {}), **refs})
        if capture.id == stored.owner_id
        else capture
        for capture in session.captures
    )


def _drawing_artifacts(
    owner_type: str,
    owner_id: str,
    role: str,
    spec_path: str,
    svg_path: str,
    png_path: str | None,
    width_px: int,
    height_px: int,
) -> tuple[ArtifactRecord, ...]:
    artifacts = [
        _drawing_part(owner_type, owner_id, role, "spec", spec_path, None, None),
        _drawing_part(owner_type, owner_id, role, "svg", svg_path, width_px, height_px),
    ]
    if png_path is not None:
        artifacts.append(
            _drawing_part(owner_type, owner_id, role, "png", png_path, width_px, height_px)
        )
    return tuple(artifacts)


def _drawing_part(
    owner_type: str,
    owner_id: str,
    role: str,
    part: str,
    path: str,
    width_px: int | None,
    height_px: int | None,
) -> ArtifactRecord:
    owner_role = f"{role}_{part}"
    content_type = {
        "spec": "application/json",
        "svg": "image/svg+xml",
        "png": "image/png",
    }[part]
    artifact_type = "drawing_spec" if part == "spec" else ("svg" if part == "svg" else "image")
    return ArtifactRecord(
        id=artifact_id(owner_type, owner_id, owner_role),
        type=artifact_type,
        label=f"{role} {part.upper()}",
        relative_path=path,
        owner=ArtifactOwnerRef(owner_type, owner_id, owner_role),
        status=ArtifactStatus.PRESENT,
        generator="SessionDrawingStore",
        file=ArtifactFileMetadata(
            width_px=width_px,
            height_px=height_px,
            content_type=content_type,
        ),
    )


def _safe_stem(owner_id: str, role: str) -> str:
    text = f"{owner_id}-{role}".strip().replace("\\", "-").replace("/", "-")
    cleaned = "".join(char if char.isalnum() or char in "-_" else "-" for char in text)
    return cleaned.strip("-") or "drawing"

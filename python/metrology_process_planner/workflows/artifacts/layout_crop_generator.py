"""Layout crop artifact generator handlers."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Protocol

from metrology_process_planner.domains.artifacts.artifact_content import artifact_content_type
from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactRecord,
    ArtifactStatus,
    PendingCapture,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.workflows.artifacts.generators import (
    ArtifactGenerationResult,
    ArtifactGenerator,
)


class LayoutImageExporter(Protocol):
    """Adapter boundary for exporting a layout region image."""

    def current_box(self) -> Box:
        """Return the currently visible layout box."""

    def center_on(self, point: Point) -> None:
        """Center the layout view on a point."""

    def export_image(self, bounds: Box, destination: Path) -> None:
        """Export the requested layout bounds to an image file."""


def layout_crop_generator(layout_view: LayoutImageExporter) -> ArtifactGenerator:
    """Return an artifact generator backed by a live layout view."""

    def regenerate_layout_crop(
        session: SessionRecord,
        artifact: ArtifactRecord,
        paths: SessionPaths,
    ) -> ArtifactGenerationResult:
        bounds = _artifact_bounds(session, artifact)
        if bounds is None:
            raise RuntimeError(f"No box geometry is available for artifact {artifact.id}.")
        relative_path = artifact.relative_path or f"images/{artifact.id}.png"
        destination = artifact_path_to_disk(paths.folder, relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        layout_view.export_image(bounds, destination)
        repaired = replace(
            artifact,
            relative_path=relative_path,
            status=ArtifactStatus.PRESENT,
            file=ArtifactFileMetadata(
                size_bytes=destination.stat().st_size if destination.exists() else None,
                content_type=artifact_content_type(relative_path) or artifact.file.content_type,
            ),
            warning_ids=(),
        )
        return ArtifactGenerationResult(repaired, session)

    return regenerate_layout_crop


def _artifact_bounds(session: SessionRecord, artifact: ArtifactRecord) -> Box | None:
    owner = artifact.owner
    if owner.owner_type == "capture":
        capture = next((item for item in session.captures if item.id == owner.owner_id), None)
        return capture.geometry.bounds if capture is not None else None
    if owner.owner_type == "pending_capture":
        pending = _pending_by_id(session, owner.owner_id)
        return pending.geometry.bounds if pending is not None else None
    return None


def _pending_by_id(session: SessionRecord, pending_id: str) -> PendingCapture | None:
    return next((item for item in session.pending_captures if item.id == pending_id), None)

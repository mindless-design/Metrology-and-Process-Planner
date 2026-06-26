"""Live layout crop repair adapter wiring."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from metrology_process_planner.domains.artifacts.artifact_content import artifact_content_type
from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactRecord,
    ArtifactStatus,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.artifacts.generator_builtins import built_in_registrations
from metrology_process_planner.workflows.artifacts.generators import (
    ArtifactGenerationResult,
    ArtifactGenerator,
    ArtifactGeneratorRegistry,
    GeneratorRegistration,
)


class LayoutCropExporter(Protocol):
    """Host boundary for exporting a layout box as an image."""

    def export_image(self, bounds: Box, destination: Path) -> ArtifactFileMetadata | None:
        """Write an image for the requested bounds and return optional file metadata."""


def layout_crop_repair_service(exporter: LayoutCropExporter) -> ArtifactRepairService:
    """Return an artifact repair service with a live layout crop handler."""

    return ArtifactRepairService(generators=_generator_registry(exporter))


def _generator_registry(exporter: LayoutCropExporter) -> ArtifactGeneratorRegistry:
    registrations = tuple(_with_layout_crop_handler(built_in_registrations(), exporter))
    return ArtifactGeneratorRegistry(registrations)


def _with_layout_crop_handler(
    registrations: Iterable[GeneratorRegistration],
    exporter: LayoutCropExporter,
) -> Iterable[GeneratorRegistration]:
    for registration in registrations:
        if registration.generator_id == "layout_crop":
            yield replace(registration, handler=_layout_crop_handler(exporter))
        else:
            yield registration


def _layout_crop_handler(exporter: LayoutCropExporter) -> ArtifactGenerator:
    def handler(
        session: SessionRecord,
        artifact: ArtifactRecord,
        paths: SessionPaths,
    ) -> ArtifactGenerationResult:
        bounds = _artifact_capture_bounds(session, artifact)
        destination = artifact_path_to_disk(paths.folder, _crop_path(artifact))
        destination.parent.mkdir(parents=True, exist_ok=True)
        metadata = exporter.export_image(bounds, destination) or ArtifactFileMetadata()
        repaired = replace(
            artifact,
            relative_path=_crop_path(artifact),
            status=ArtifactStatus.PRESENT,
            generator="layout_crop",
            file=_file_metadata(metadata, destination),
            warning_ids=(),
        )
        return ArtifactGenerationResult(repaired, session)

    return handler


def _artifact_capture_bounds(session: SessionRecord, artifact: ArtifactRecord) -> Box:
    for capture in session.captures:
        if capture.id == artifact.owner.owner_id and capture.geometry.bounds is not None:
            return capture.geometry.bounds.normalized()
    raise RuntimeError(f"No box capture geometry found for artifact {artifact.id}.")


def _crop_path(artifact: ArtifactRecord) -> str:
    return artifact.relative_path or f"images/{artifact.owner.owner_id}.png"


def _file_metadata(metadata: ArtifactFileMetadata, destination: Path) -> ArtifactFileMetadata:
    content_type = metadata.content_type or artifact_content_type(destination.name) or "image/png"
    return replace(metadata, content_type=content_type)

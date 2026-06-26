"""Shared fixtures for artifact lifecycle tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    CaptureGeometry,
    CaptureRecord,
    ModeRegistry,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import ArtifactScanner


def session(artifacts=None) -> SessionRecord:
    """Return a minimal session with one capture and one measurement."""

    measurement = MeasurementRecord("meas-001", "Gate CD", Point(1, 1), Point(2, 1))
    capture = CaptureRecord(
        "cap-001",
        "Site 1",
        CaptureGeometry.box(Box(0, 0, 5, 5)),
        "2026-06-24T00:00:00Z",
        measurements=(measurement,),
    )
    return SessionRecord(
        "session-001",
        "Artifact Demo",
        SessionMode.SIMPLE_CAPTURE,
        "2026-06-24T00:00:00Z",
        "2026-06-24T00:00:00Z",
        captures=(capture,),
        artifacts=artifacts or {},
    )


def artifact(
    artifact_id: str,
    path: str = "images/cap-001.png",
    owner: ArtifactOwnerRef | None = None,
    dependencies: tuple[ArtifactDependencyRef, ...] = (),
) -> ArtifactRecord:
    """Return a regenerable capture-owned artifact record."""

    return ArtifactRecord(
        artifact_id,
        "captured_site_image",
        artifact_id,
        path,
        owner or ArtifactOwnerRef("capture", "cap-001", "crop"),
        dependencies=dependencies,
        repair=ArtifactRepairMetadata(regenerable=True),
    )


def scan_with_file(
    source: SessionRecord,
    relative_path: str,
    mode_registry: ModeRegistry | None = None,
):
    """Scan a session after materializing one artifact file."""

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = SessionPaths.for_folder(Path(temp_dir))
        paths.ensure_created()
        destination = paths.folder / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("artifact", encoding="utf-8")
        return ArtifactScanner().scan_session(source, paths, mode_registry)


def temp_paths() -> SessionPaths:
    """Return a temporary session path bundle."""

    return SessionPaths.for_folder(Path(tempfile.mkdtemp()))


lifecycle_session = session
lifecycle_artifact = artifact


lifecycle_session = session
lifecycle_artifact = artifact

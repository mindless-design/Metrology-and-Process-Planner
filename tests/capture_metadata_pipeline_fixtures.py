"""Fixtures for capture metadata and annotation pipeline tests."""

from __future__ import annotations

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    CaptureGeometry,
    CaptureRecord,
    GeometryKind,
    SessionMode,
    SessionRecord,
    SourceLayoutContext,
)


def simple_capture() -> CaptureRecord:
    """Return a saved box capture."""

    return CaptureRecord(
        id="cap-001",
        label="Site 001",
        geometry=CaptureGeometry.box(Box(0, 0, 10, 10)),
        created_at="2026-06-24T00:00:00Z",
    )


def line_feature_capture() -> CaptureRecord:
    """Return a capture with a nested feature line and measurement."""

    return CaptureRecord(
        id="cap-001",
        label="Profile Site 001",
        geometry=CaptureGeometry(
            kind=GeometryKind.COMPOSITE,
            bounds=Box(0, 0, 10, 10),
            features=(
                {
                    "id": "feat-001",
                    "label": "Profile Line",
                    "role": "profilometry_line",
                    "kind": "line",
                    "geometry": {
                        "shape": "line",
                        "start": {"x": 1, "y": 1},
                        "end": {"x": 9, "y": 9},
                    },
                },
            ),
        ),
        created_at="2026-06-24T00:00:00Z",
        measurements=(MeasurementRecord("meas-001", "CD", Point(2, 2), Point(4, 2)),),
    )


def session_with_capture(capture: CaptureRecord) -> SessionRecord:
    """Return a session with site image and annotation placeholders."""

    site = ArtifactRecord(
        "capture-cap-001-site_image",
        "image",
        "Site Image",
        "images/cap-001.png",
        ArtifactOwnerRef("capture", "cap-001", "site_image"),
        status=ArtifactStatus.PRESENT,
        file=ArtifactFileMetadata(content_type="image/png"),
    )
    annotation = ArtifactRecord(
        "capture-cap-001-line_annotation",
        "svg",
        "Line Annotation",
        "drawings/cap-001-line_annotation.svg",
        ArtifactOwnerRef("capture", "cap-001", "line_annotation"),
        status=ArtifactStatus.PLACEHOLDER,
        file=ArtifactFileMetadata(content_type="image/svg+xml"),
    )
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.PROFILOMETRY_PLANNER,
        created_at="2026-06-24T00:00:00Z",
        updated_at="2026-06-24T00:00:00Z",
        source_layout=SourceLayoutContext(
            layout_path="C:/layouts/layout.gds",
            layout_name="layout.gds",
            top_cell="TOP",
        ),
        captures=(capture,),
        artifacts={site.id: site, annotation.id: annotation},
    )

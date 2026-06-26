"""Capture geometry and artifact inspector-field helpers."""

from __future__ import annotations

from typing import Optional

from metrology_process_planner.domains.artifacts.artifact_query import (
    artifact_for_role,
    artifacts_for_owner,
)
from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    CaptureRecord,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.workflows.editor.adapter_metadata_lookup import mapping
from metrology_process_planner.workflows.editor.view_models import MetadataField


def capture_geometry_fields(
    session: SessionRecord,
    capture: CaptureRecord,
) -> tuple[MetadataField, ...]:
    """Return read-only capture geometry fields for the inspector."""

    primary = capture.geometry.primary_metadata()
    if primary is None:
        return (
            MetadataField(
                "coordinate_mode",
                "Coordinate Mode",
                session.coordinates.origin,
                read_only=True,
            ),
            MetadataField("units", "Units", session.coordinates.units, read_only=True),
        )
    center = mapping(primary.get("center"))
    bounds = mapping(primary.get("bounds"))
    return (
        MetadataField("center", "Center", point_text(center), read_only=True),
        MetadataField("bounds", "Bounds", bounds_text(bounds), read_only=True),
        MetadataField("width", "Width", str(primary.get("width", "")), read_only=True),
        MetadataField("height", "Height", str(primary.get("height", "")), read_only=True),
        MetadataField(
            "coordinate_mode",
            "Coordinate Mode",
            str(primary.get("coordinate_mode", "")),
            read_only=True,
        ),
        MetadataField("units", "Units", str(primary.get("units", "")), read_only=True),
        MetadataField(
            "source_layout",
            "Source Layout",
            session.source_layout.layout_path,
            read_only=True,
        ),
        MetadataField("top_cell", "Top Cell", session.source_layout.top_cell, read_only=True),
    )


def capture_artifact_fields(
    session: SessionRecord,
    capture: CaptureRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[MetadataField, ...]:
    """Return read-only capture artifact status fields."""

    artifacts = tuple(
        artifact
        for artifact in artifacts_for_owner(session.artifacts or {}, "capture", capture.id)
        if artifact_visible_for_session(session, artifact, mode_registry)
    )
    site = artifact_for_role(artifacts, "site_image") or artifact_for_role(artifacts, "crop")
    annotation = annotation_artifact(artifacts)
    return (
        MetadataField(
            "site_image_status",
            "Site Image",
            site.status.value if site is not None else "missing",
            read_only=True,
        ),
        MetadataField(
            "annotation_status",
            "Annotation",
            annotation.status.value if annotation is not None else "missing",
            read_only=True,
        ),
    )


def point_text(point: dict[str, object]) -> str:
    """Return a compact coordinate pair string."""

    return f"{point.get('x', '')}, {point.get('y', '')}"


def bounds_text(bounds: dict[str, object]) -> str:
    """Return a compact bounds string."""

    return (
        f"L {bounds.get('left', '')}, R {bounds.get('right', '')}, "
        f"B {bounds.get('bottom', '')}, T {bounds.get('top', '')}"
    )


def annotation_artifact(artifacts: tuple[ArtifactRecord, ...]) -> Optional[ArtifactRecord]:
    """Return the preferred annotation artifact for a capture."""

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

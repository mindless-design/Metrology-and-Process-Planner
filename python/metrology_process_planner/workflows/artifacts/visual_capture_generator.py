"""Capture-owned visual artifact polish generators."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactRecord,
    ArtifactStatus,
    CaptureRecord,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.rendering.annotation_planner import build_layout_annotation_scene
from metrology_process_planner.rendering.svg_renderer import render_scene_to_svg
from metrology_process_planner.rendering.visual_labels import SiteLabelBuilder
from metrology_process_planner.workflows.artifacts.visual_capture_overview import (
    expanded_bounds,
    render_site_overview_svg,
)
from metrology_process_planner.workflows.artifacts.visual_capture_source import (
    image_href as _image_href,
)
from metrology_process_planner.workflows.artifacts.visual_capture_source import (
    with_source_image_metadata as _with_source_image_metadata,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    annotation_role as _annotation_role,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    artifact_record as _artifact_record,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    capture_by_id as _capture_by_id,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    normalized_annotation_role as _normalized_annotation_role,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    raw_site_artifact as _raw_site_artifact,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    svg_path as _svg_path,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    warning as _warning,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    with_capture_artifact as _with_capture_artifact,
)
from metrology_process_planner.workflows.artifacts.visual_capture_support import (
    write_text_artifact as _write,
)
from metrology_process_planner.workflows.artifacts.visual_capture_svg import (
    labeled_site_svg as _labeled_site_svg,
)
from metrology_process_planner.workflows.artifacts.visual_capture_svg import (
    placeholder_svg as _placeholder_svg,
)

GENERATOR_ID = "visual_capture_polish"


def generate_visual_artifacts_for_capture(
    session: SessionRecord,
    capture_id: str,
    paths: SessionPaths,
) -> SessionRecord:
    """Generate the default report-ready visual artifact set for one capture."""

    capture = _capture_by_id(session, capture_id)
    if capture is None:
        return session
    current = generate_labeled_site_artifact(session, capture, paths)
    capture = _capture_by_id(current, capture_id) or capture
    current = generate_site_overview_artifact(current, capture, paths)
    capture = _capture_by_id(current, capture_id) or capture
    return generate_annotation_artifact(current, capture, paths, _annotation_role(capture))


def generate_labeled_site_artifact(
    session: SessionRecord,
    capture: CaptureRecord,
    paths: SessionPaths,
) -> SessionRecord:
    """Generate a labeled SVG wrapper without modifying the raw site image."""

    label = SiteLabelBuilder().build(session, capture)
    raw = _raw_site_artifact(session, capture)
    role = "site_image_labeled"
    artifact = _artifact_record(capture, role, role, _svg_path(capture.id, role), label)
    warning = _missing_site_warning(raw, artifact)
    svg_text = _labeled_site_svg(
        raw,
        label,
        warning is not None,
        image_href=_source_href(paths, artifact, raw),
    )
    _write(paths, artifact.relative_path, svg_text)
    if raw is not None:
        artifact = _with_source_image_metadata(artifact, raw)
    if warning is not None:
        artifact = replace(artifact, status=ArtifactStatus.PLACEHOLDER, warning_ids=(warning.id,))
    warnings = () if warning is None else (warning,)
    return _with_capture_artifact(session, capture.id, artifact, warnings)


def _missing_site_warning(
    raw: ArtifactRecord | None,
    artifact: ArtifactRecord,
) -> WarningRecord | None:
    if raw is not None:
        return None
    return _warning(artifact, "SITE_IMAGE_SOURCE_MISSING")


def _source_href(
    paths: SessionPaths,
    artifact: ArtifactRecord,
    raw: ArtifactRecord | None,
) -> str:
    if raw is None:
        return ""
    return _image_href(paths, artifact.relative_path, raw)


def generate_site_overview_artifact(
    session: SessionRecord,
    capture: CaptureRecord,
    paths: SessionPaths,
    role: str = "site_overview_image",
) -> SessionRecord:
    """Generate a capture-scoped overview image with expanded context and full site label."""

    label = SiteLabelBuilder().build(session, capture)
    artifact = _artifact_record(capture, role, role, _svg_path(capture.id, role), label)
    if capture.geometry.bounds is None:
        warning = _warning(artifact, "SITE_OVERVIEW_SOURCE_MISSING")
        _write(paths, artifact.relative_path, _placeholder_svg(label, warning.message))
        artifact = replace(artifact, status=ArtifactStatus.PLACEHOLDER, warning_ids=(warning.id,))
        return _with_capture_artifact(session, capture.id, artifact, (warning,))
    region = expanded_bounds(capture.geometry.bounds, 4.0)
    svg_text, canvas_size = render_site_overview_svg(
        session,
        capture.id,
        region,
        label,
        f"{session.id}-{capture.id}-{role}",
    )
    _write(paths, artifact.relative_path, svg_text)
    artifact = replace(
        artifact,
        file=ArtifactFileMetadata(
            width_px=canvas_size[0],
            height_px=canvas_size[1],
            content_type="image/svg+xml",
        ),
        extensions={
            **dict(artifact.extensions or {}),
            "overview_context_policy": "capture_bounds_expanded_4x",
            "overview_region": region.to_dict(),
            "label_policy_id": "site_label_standard",
        },
    )
    return _with_capture_artifact(session, capture.id, artifact, ())


def generate_annotation_artifact(
    session: SessionRecord,
    capture: CaptureRecord,
    paths: SessionPaths,
    role: str = "line_annotation_image",
) -> SessionRecord:
    """Generate a polished line, point, or measurement annotation SVG artifact."""

    normalized_role = _normalized_annotation_role(role)
    label = SiteLabelBuilder().build(session, capture)
    artifact = _artifact_record(
        capture,
        normalized_role,
        normalized_role,
        _svg_path(capture.id, normalized_role),
        label,
    )
    try:
        raw = _raw_site_artifact(session, capture)
        base = (
            None
            if raw is None
            else replace(raw, relative_path=_image_href(paths, artifact.relative_path, raw))
        )
        scene = build_layout_annotation_scene(
            capture,
            base,
            normalized_role,
        )
    except ValueError as exc:
        warning = _warning(artifact, "ANNOTATION_TRANSFORM_FAILED", str(exc))
        _write(paths, artifact.relative_path, _placeholder_svg(label, warning.message))
        artifact = replace(artifact, status=ArtifactStatus.PLACEHOLDER, warning_ids=(warning.id,))
        return _with_capture_artifact(session, capture.id, artifact, (warning,))
    _write(paths, artifact.relative_path, render_scene_to_svg(scene))
    if raw is not None:
        artifact = _with_source_image_metadata(artifact, raw)
    return _with_capture_artifact(session, capture.id, artifact, ())

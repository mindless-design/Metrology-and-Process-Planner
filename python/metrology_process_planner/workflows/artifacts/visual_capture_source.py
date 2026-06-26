"""Source-image embedding helpers for capture visual artifacts."""

from __future__ import annotations

import base64
from dataclasses import replace
from mimetypes import guess_type

from metrology_process_planner.domains.session import ArtifactRecord
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.workflows.artifacts.visual_capture_support import relative_href


def image_href(paths: SessionPaths, svg_relative_path: str, raw: ArtifactRecord) -> str:
    """Return a data URI for a source image, or a local href fallback."""

    source = artifact_path_to_disk(paths.folder, raw.relative_path)
    if not source.exists():
        return relative_href(svg_relative_path, raw.relative_path)
    content_type = raw.file.content_type or guess_type(source.name)[0] or "image/png"
    encoded = base64.b64encode(source.read_bytes()).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def with_source_image_metadata(
    artifact: ArtifactRecord,
    raw: ArtifactRecord,
) -> ArtifactRecord:
    """Attach source-image provenance metadata to a derived visual artifact."""

    return replace(
        artifact,
        extensions={
            **dict(artifact.extensions or {}),
            "source_image_artifact_id": raw.id,
            "source_image_relative_path": raw.relative_path,
            "source_image_embedding": "data_uri",
        },
    )

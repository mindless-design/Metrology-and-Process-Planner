"""Generate capture-image manifest items for the visual quality gallery."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from metrology_process_planner.testing.visual_quality import VisualManifestItem


def capture_items(output_root: Path) -> list[VisualManifestItem]:
    """Return rendered capture visual manifest items."""

    from PIL import Image, ImageDraw

    from metrology_process_planner.persistence.paths import SessionPaths

    _write_site_source_image(output_root, Image, ImageDraw)
    paths = SessionPaths.for_folder(output_root)
    session = _line_session(paths)
    point_session = _point_session(paths)
    return [
        _raw_site_item(output_root),
        *_capture_manifest_rows(session, output_root),
        *_capture_manifest_rows(point_session, output_root),
    ]


def _line_session(paths: Any) -> Any:
    from tests.capture_metadata_pipeline_fixtures import line_feature_capture, session_with_capture

    from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
        generate_annotation_artifact,
        generate_labeled_site_artifact,
        generate_site_overview_artifact,
    )

    line_capture = line_feature_capture()
    session = session_with_capture(line_capture)
    session = generate_labeled_site_artifact(session, line_capture, paths)
    session = generate_site_overview_artifact(session, session.captures[0], paths)
    session = generate_annotation_artifact(
        session,
        session.captures[0],
        paths,
        "line_annotation_image",
    )
    session = generate_annotation_artifact(
        session,
        session.captures[0],
        paths,
        "measurement_annotation_image",
    )
    return session


def _point_session(paths: Any) -> Any:
    from tests.capture_metadata_pipeline_fixtures import session_with_capture, simple_capture

    from metrology_process_planner.domains.capture.capture_geometry import CaptureGeometry
    from metrology_process_planner.domains.geometry import Point
    from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
        generate_annotation_artifact,
    )

    point_capture = replace(
        simple_capture(),
        type="ellipsometry",
        geometry=CaptureGeometry(
            kind=simple_capture().geometry.kind,
            bounds=simple_capture().geometry.bounds,
            features=(_point_feature(Point),),
        ),
    )
    point_session = generate_annotation_artifact(
        session_with_capture(point_capture),
        point_capture,
        paths,
        "point_annotation_image",
    )
    return point_session


def _capture_manifest_rows(session: Any, output_root: Path) -> list[VisualManifestItem]:
    rows: list[VisualManifestItem] = []
    capture = session.captures[0]
    role_types = {
        "site_image_labeled": "labeled_site_image",
        "site_overview_image": "site_specific_overview_image",
        "line_annotation_image": "line_annotation_image",
        "point_annotation_image": "point_annotation_image",
        "measurement_annotation_image": "measurement_annotation_image",
    }
    for role, visual_type in role_types.items():
        artifact_id = dict(capture.artifact_refs or {}).get(role)
        if artifact_id:
            rows.append(_capture_manifest_row(session, artifact_id, role, visual_type, output_root))
    return rows


def _raw_site_item(output_root: Path) -> VisualManifestItem:
    metadata_path = "images/cap-001.raw-site.metadata.json"
    _write_json(output_root / metadata_path, _raw_site_metadata())
    return VisualManifestItem(
        artifact_id="capture:raw-site",
        visual_type="raw_site_image",
        source_fixture="capture_site",
        mode="profilometry",
        render_profile="raw",
        image_path="images/cap-001.png",
        status="pending",
        metadata_path=metadata_path,
        source_artifact_id="capture-cap-001-site_image",
        capture_id="cap-001",
        metadata={"preserves_raw_capture": True},
    )


def _capture_manifest_row(
    session: Any,
    artifact_id: str,
    role: str,
    visual_type: str,
    output_root: Path,
) -> VisualManifestItem:
    capture = session.captures[0]
    artifact = dict(session.artifacts or {})[artifact_id]
    metadata_path = (
        f"{Path(artifact.relative_path).with_suffix('')}.metadata.json".replace("\\", "/")
    )
    metadata = _capture_metadata(artifact, role, visual_type)
    _write_json(output_root / metadata_path, metadata)
    return VisualManifestItem(
        artifact_id=artifact.id,
        visual_type=visual_type,
        source_fixture="capture_site",
        mode=str(session.mode.value),
        render_profile=role,
        image_path=artifact.relative_path,
        status="pending",
        warnings=tuple(artifact.warning_ids),
        metadata_path=metadata_path,
        source_artifact_id=str(
            artifact.extensions.get("source_image_artifact_id")
            or f"capture-{capture.id}-site_image"
        ),
        capture_id=capture.id,
        metadata=metadata,
    )


def _capture_metadata(artifact: Any, role: str, visual_type: str) -> dict[str, Any]:
    return {
        "artifact_id": artifact.id,
        "comparison": "not_configured",
        "preserves_raw_capture": role != "site_image",
        "role": role,
        "source_artifact_id": artifact.extensions.get("source_image_artifact_id", ""),
        "source_image_relative_path": artifact.extensions.get("source_image_relative_path", ""),
        "status": str(artifact.status.value),
        "visual_type": visual_type,
        "warnings": list(artifact.warning_ids),
    }


def _raw_site_metadata() -> dict[str, object]:
    return {
        "capture_id": "cap-001",
        "preserves_raw_capture": True,
        "source_artifact_id": "capture-cap-001-site_image",
        "visual_type": "raw_site_image",
    }


def _point_feature(point_type: Any) -> dict[str, Any]:
    return {
        "id": "point-001",
        "kind": "ellipsometry_point",
        "label": "Film Stack Point",
        "geometry": {"shape": "point", "point": point_type(9.5, 9.5).to_dict()},
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_site_source_image(output_root: Path, image_type: Any, draw_type: Any) -> None:
    image_dir = output_root / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    image = image_type.new("RGB", (1024, 768), "#f8fafc")
    draw = draw_type.Draw(image)
    draw.rectangle((170, 150, 850, 610), outline="#334155", width=4)
    draw.line((250, 530, 780, 220), fill="#2563eb", width=6)
    draw.ellipse((242, 522, 258, 538), fill="#2563eb")
    draw.ellipse((772, 212, 788, 228), fill="#2563eb")
    draw.text((180, 120), "Synthetic process site", fill="#111827")
    image.save(image_dir / "cap-001.png")

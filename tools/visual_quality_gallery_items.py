"""Generate manifest items for the visual quality gallery."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.testing.visual_quality import VisualManifestItem

PROCESS_CASES = (
    ("profilometry_surface_profile", "profilometry_surface_recipe", "profilometry_surface_profile"),
    ("ellipsometry_point_stack", "simple_stack_recipe", "point_stack_schematic"),
    ("fib_full_stack_compressed", "fib_full_stack_recipe", "fib_full_stack_compressed"),
    ("process_flow_frame", "process_flow_recipe", "process_flow_frame"),
    ("thin_conformal_liner", "conformal_liner_recipe", "illustrative_process_cross_section"),
    ("physical_cross_section", "simple_stack_recipe", "physical_cross_section"),
)


def process_items(root: Path, output_root: Path) -> list[VisualManifestItem]:
    """Return rendered process visual manifest items."""

    from metrology_process_planner.domains.process import (
        HybridCrossSectionSolver,
        SolverInput,
        SolverOptions,
    )
    from metrology_process_planner.rendering.cross_section import (
        CrossSectionOutputSpec,
        SvgCrossSectionRenderer,
        build_cross_section_scene,
        built_in_render_profile,
        scene_to_dict,
    )

    recipe_root = root / "tests" / "fixtures" / "recipes"
    renderer = SvgCrossSectionRenderer()
    items: list[VisualManifestItem] = []
    for visual_type, recipe_id, profile_id in PROCESS_CASES:
        recipe = _recipe(recipe_root, recipe_id)
        result = HybridCrossSectionSolver().solve(
            SolverInput(recipe, SolverOptions(x_min=0.0, x_max=10.0, sample_count=61))
        )
        profile = built_in_render_profile(profile_id)
        scene = build_cross_section_scene(
            result,
            profile,
            materials=recipe.materials,
            scene_id=visual_type,
        )
        scene_name = f"process/{visual_type}.scene.json"
        svg_name = f"process/{visual_type}.svg"
        _write_json(output_root / scene_name, scene_to_dict(scene))
        renderer.render(
            scene,
            CrossSectionOutputSpec(
                output_path=str(output_root / svg_name),
                artifact_id=f"process:{visual_type}",
            ),
        )
        items.append(_process_item(scene, visual_type, recipe_id, profile_id, svg_name, scene_name))
    return items


def capture_items(output_root: Path) -> list[VisualManifestItem]:
    """Return rendered capture visual manifest items."""

    from PIL import Image, ImageDraw
    from tests.capture_metadata_pipeline_fixtures import (
        line_feature_capture,
        session_with_capture,
        simple_capture,
    )

    from metrology_process_planner.domains.capture.capture_geometry import CaptureGeometry
    from metrology_process_planner.domains.geometry import Point
    from metrology_process_planner.persistence.paths import SessionPaths
    from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
        generate_annotation_artifact,
        generate_labeled_site_artifact,
        generate_site_overview_artifact,
    )

    _write_site_source_image(output_root, Image, ImageDraw)
    paths = SessionPaths.for_folder(output_root)
    line_capture = line_feature_capture()
    session = session_with_capture(line_capture)
    session = generate_labeled_site_artifact(session, line_capture, paths)
    session = generate_site_overview_artifact(session, session.captures[0], paths)
    session = generate_annotation_artifact(session, session.captures[0], paths,
                                           "line_annotation_image")
    session = generate_annotation_artifact(session, session.captures[0], paths,
                                           "measurement_annotation_image")
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
    return [
        VisualManifestItem("capture:raw-site", "raw_site_image", "capture_site",
                           "profilometry", "raw", "images/cap-001.png", "pending"),
        *_capture_manifest_rows(session),
        *_capture_manifest_rows(point_session),
    ]


def _process_item(
    scene: Any,
    visual_type: str,
    recipe_id: str,
    profile_id: str,
    svg_name: str,
    scene_name: str,
) -> VisualManifestItem:
    return VisualManifestItem(
        f"process:{visual_type}",
        visual_type,
        recipe_id,
        scene.render_mode_id,
        profile_id,
        svg_name,
        "pending",
        scene.warnings,
        scene_name,
    )


def _capture_manifest_rows(session: Any) -> list[VisualManifestItem]:
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
            rows.append(_capture_manifest_row(session, artifact_id, role, visual_type))
    return rows


def _capture_manifest_row(
    session: Any,
    artifact_id: str,
    role: str,
    visual_type: str,
) -> VisualManifestItem:
    artifact = dict(session.artifacts or {})[artifact_id]
    return VisualManifestItem(
        artifact.id,
        visual_type,
        "capture_site",
        str(session.mode.value),
        role,
        artifact.relative_path,
        "pending",
        tuple(artifact.warning_ids),
        "",
    )


def _point_feature(point_type: Any) -> dict[str, Any]:
    return {
        "id": "point-001",
        "kind": "ellipsometry_point",
        "label": "Film Stack Point",
        "geometry": {"shape": "point", "point": point_type(9.5, 9.5).to_dict()},
    }


def _recipe(recipe_root: Path, recipe_id: str) -> ProcessRecipe:
    return ProcessRecipe.from_dict(json.loads((recipe_root / f"{recipe_id}.json").read_text()))


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

"""Shared KLayout process regression probe script fragments."""

from __future__ import annotations

import json


def report_from_stdout(stdout: str) -> dict[str, object]:
    """Extract the REPORT JSON payload from a KLayout probe."""

    for line in stdout.splitlines():
        if line.startswith("REPORT="):
            return json.loads(line.removeprefix("REPORT="))
    raise AssertionError(f"KLayout probe did not emit REPORT JSON. stdout={stdout!r}")


COMMON_SCRIPT = r"""
import json
import tempfile
from pathlib import Path

from metrology_process_planner.domains.process import (
    HybridCrossSectionSolver,
    LayerReference,
    ProcessRecipe,
    SolverInput,
    SolverOptions,
)
from metrology_process_planner.infrastructure.klayout.geometry import KLayoutGeometryExtractor
from metrology_process_planner.infrastructure.klayout.qt_rasterizer import QtSvgRasterizer
from metrology_process_planner.rendering.cross_section import (
    CrossSectionOutputSpec,
    SvgCrossSectionRenderer,
    build_cross_section_scene,
    built_in_render_profile,
)

ROOT = Path.cwd()
GDS = ROOT / "tests" / "fixtures" / "gds" / "process_planner_testchip.gds"
RECIPES = ROOT / "tests" / "fixtures" / "recipes"
GOLDEN = ROOT / "tests" / "golden"
extractor = KLayoutGeometryExtractor()
layout = extractor.load_layout(GDS)

def recipe(recipe_id):
    return ProcessRecipe.from_dict(json.loads((RECIPES / (recipe_id + ".json")).read_text()))

def solve(recipe_id):
    return HybridCrossSectionSolver().solve(
        SolverInput(
            recipe(recipe_id),
            SolverOptions(
                x_min=0.0,
                x_max=10.0,
                sample_count=31,
                point_sample_xs=(1.0, 5.0, 9.0),
                cutline_x_min=0.0,
                cutline_x_max=10.0,
            ),
        )
    )

def stack_signature(result):
    return [
        [round(column.x, 3), [interval.material_id for interval in column.intervals]]
        for column in result.frames[-1].profile.columns
    ]

def solver_summary(recipe_id):
    result = solve(recipe_id)
    final = result.frames[-1]
    top_surface = [round(column.top, 3) for column in final.profile.columns]
    return {
        "recipe_id": recipe_id,
        "frame_count": len(result.frames),
        "final_step": final.step_id,
        "materials": sorted({
            item.material_id
            for column in final.profile.columns
            for item in column.intervals
        }),
        "diagnostics": sorted({
            item.code for item in result.diagnostics
            if item.code != "STACK_INVARIANT_VIOLATION"
        }),
        "stack_signature": stack_signature(result),
        "top_min": min(top_surface),
        "top_max": max(top_surface),
        "point_sample_count": len(result.point_samples),
        "cutline_sample_count": len(result.cutline_samples),
    }

def render_summary(recipe_id, profile_id):
    process_recipe = recipe(recipe_id)
    result = HybridCrossSectionSolver().solve(
        SolverInput(process_recipe, SolverOptions(x_min=0.0, x_max=10.0, sample_count=31))
    )
    scene = build_cross_section_scene(
        result,
        built_in_render_profile(profile_id),
        materials=process_recipe.materials,
        scene_id=recipe_id + "." + profile_id,
        title=process_recipe.name,
    )
    material_counts = {}
    for shape in scene.material_shapes:
        material_counts[shape.material_id] = material_counts.get(shape.material_id, 0) + 1
    return {
        "recipe_id": recipe_id,
        "profile_id": profile_id,
        "render_mode_id": scene.render_mode_id,
        "shape_count": len(scene.material_shapes),
        "materials": dict(sorted(material_counts.items())),
        "label_count": len(scene.labels),
        "warnings": sorted(scene.warnings),
        "compression_enabled": scene.compression_metadata.enabled,
        "compressed_materials": sorted(scene.compression_metadata.affected_materials),
        "thin_layer_shape_count": sum(
            1 for shape in scene.material_shapes if shape.exaggerated_flag
        ),
    }

def golden_solver(recipe_id):
    return json.loads((GOLDEN / "solver" / (recipe_id + ".expected.json")).read_text())

def golden_render(recipe_id, profile_id):
    return json.loads(
        (GOLDEN / "render" / (recipe_id + "." + profile_id + ".expected.json")).read_text()
    )

def emit(payload):
    print("REPORT=" + json.dumps(payload, sort_keys=True))
"""

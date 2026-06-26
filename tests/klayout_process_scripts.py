"""KLayout process regression probe scripts."""

from __future__ import annotations

from tests.klayout_process_common import COMMON_SCRIPT

LOAD_GDS_SCRIPT = COMMON_SCRIPT + r"""
layers = (
    LayerReference("layout", 2, 0, "POLY"),
    LayerReference("layout", 4, 0, "METAL1"),
    LayerReference("layout", 11, 0, "GRID"),
)
def counts(cell_name):
    summary = extractor.summarize_cell(layout, cell_name, layers)
    return {item.name: item.shape_count for item in summary.layer_summaries}
emit({
    "top_cell": extractor.top_cell_name(layout),
    "cell_names": extractor.cell_names(layout),
    "simple_line_space": counts("simple_line_space"),
    "grid_capture_test": counts("grid_capture_test"),
})
"""

EXTRACT_INTERVALS_SCRIPT = COMMON_SCRIPT + r"""
def intervals(cell_name, layer, datatype, name, y):
    extracted = extractor.extract_cutline_intervals(
        layout,
        cell_name,
        LayerReference("layout", layer, datatype, name),
        y,
    )
    return [[round(item.x_min, 3), round(item.x_max, 3)] for item in extracted.intervals]
emit({
    "line_space_first_two": intervals("simple_line_space", 4, 0, "METAL1", 6.0)[:2],
    "trench": intervals("trench_via_etch", 7, 0, "TRENCH", 7.5),
    "liner": intervals("conformal_liner_challenge", 8, 0, "LINER_TEST", 36.0),
})
"""

SOLVER_SCRIPT = COMMON_SCRIPT + r"""
emit({
    "expected_simple": golden_solver("simple_stack_recipe"),
    "actual_simple": solver_summary("simple_stack_recipe"),
    "expected_liner": golden_solver("conformal_liner_recipe"),
    "actual_liner": solver_summary("conformal_liner_recipe"),
    "expected_taper": golden_solver("tapered_etch_recipe"),
    "actual_taper": solver_summary("tapered_etch_recipe"),
})
"""

RENDER_SCENE_SCRIPT = COMMON_SCRIPT + r"""
emit({
    "expected_liner": golden_render(
        "conformal_liner_recipe",
        "illustrative_process_cross_section",
    ),
    "actual_liner": render_summary(
        "conformal_liner_recipe",
        "illustrative_process_cross_section",
    ),
    "expected_profile": golden_render(
        "profilometry_surface_recipe",
        "profilometry_surface_profile",
    ),
    "actual_profile": render_summary(
        "profilometry_surface_recipe",
        "profilometry_surface_profile",
    ),
    "expected_fib": golden_render(
        "fib_full_stack_recipe",
        "fib_full_stack_compressed",
    ),
    "actual_fib": render_summary(
        "fib_full_stack_recipe",
        "fib_full_stack_compressed",
    ),
})
"""

RASTERIZE_SCRIPT = COMMON_SCRIPT + r"""
process_recipe = recipe("conformal_liner_recipe")
result = HybridCrossSectionSolver().solve(
    SolverInput(process_recipe, SolverOptions(x_min=0.0, x_max=10.0, sample_count=31))
)
scene = build_cross_section_scene(
    result,
    built_in_render_profile("illustrative_process_cross_section"),
    materials=process_recipe.materials,
    scene_id="klayout-rasterized-conformal",
    title=process_recipe.name,
)
with tempfile.TemporaryDirectory() as temp_dir:
    target = Path(temp_dir) / "conformal.png"
    render_result = SvgCrossSectionRenderer(QtSvgRasterizer()).render(
        scene,
        CrossSectionOutputSpec(output_path=str(target), artifact_id="artifact-klayout-conformal"),
    )
    path = Path(render_result.path)
    emit({
        "status": render_result.status,
        "png_exists": path.exists(),
        "png_size": path.stat().st_size if path.exists() else 0,
        "render_mode_id": render_result.render_metadata["render_mode_id"],
    })
"""

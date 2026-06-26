import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.rendering.cross_section import (
    CrossSectionOutputSpec,
    SvgCrossSectionRenderer,
    build_cross_section_scene,
    built_in_render_profile,
    scene_from_dict,
    scene_to_dict,
)
from tests.cross_section_rendering_fixtures import (
    MATERIALS,
    conformal_liner_result,
    fib_full_stack_result,
    profilometry_surface_result,
    simple_stack_result,
)

if __name__ == "__main__":
    unittest.main()


class CrossSectionRenderingPipelineTestsPart1(unittest.TestCase):
    def test_built_in_profile_validation(self) -> None:
        profiles = [
            "physical_cross_section",
            "illustrative_process_cross_section",
            "profilometry_surface_profile",
            "fib_full_stack_compressed",
            "process_flow_frame",
            "point_stack_schematic",
        ]

        for profile_id in profiles:
            self.assertEqual(profile_id, built_in_render_profile(profile_id).profile_id)

    def test_physical_scene_preserves_proportional_geometry(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(simple_stack_result(), profile, materials=MATERIALS)

        metal = next(shape for shape in scene.material_shapes if shape.material_id == "metal")

        self.assertEqual("proportional_physical", scene.render_mode_id)
        self.assertEqual(metal.physical_bounds, metal.visual_bounds)
        self.assertTrue(scene.scale_bars)
        self.assertTrue(any(label.text.startswith("Metal") for label in scene.labels))

    def test_illustrative_scene_exaggerates_thin_conformal_liner_with_metadata(self) -> None:
        profile = built_in_render_profile("illustrative_process_cross_section")
        scene = build_cross_section_scene(conformal_liner_result(), profile, materials=MATERIALS)

        liners = [shape for shape in scene.material_shapes if shape.material_id == "al2o3"]

        self.assertTrue(any(shape.exaggerated_flag for shape in liners))
        self.assertIn("RENDER_THIN_LAYER_EXAGGERATED", scene.warnings)
        self.assertTrue(scene.compression_metadata.min_thickness_overrides)
        self.assertTrue(scene.legend.show_exaggeration_notes if scene.legend else False)

    def test_profilometry_filter_keeps_surface_context_only(self) -> None:
        profile = built_in_render_profile("profilometry_surface_profile")
        scene = build_cross_section_scene(
            profilometry_surface_result(),
            profile,
            materials=MATERIALS,
        )

        material_ids = {shape.material_id for shape in scene.material_shapes}

        self.assertEqual({"dielectric"}, material_ids)
        self.assertEqual("profilometry_surface", scene.render_mode_id)
        self.assertTrue(scene.surface_profiles)

    def test_fib_full_stack_compresses_substrate_and_records_break_marks(self) -> None:
        profile = built_in_render_profile("fib_full_stack_compressed")
        scene = build_cross_section_scene(fib_full_stack_result(), profile, materials=MATERIALS)

        substrate = next(shape for shape in scene.material_shapes if shape.material_id == "si")

        self.assertTrue(substrate.compressed_flag)
        self.assertTrue(scene.compression_metadata.enabled)
        self.assertTrue(scene.compression_metadata.break_marks)
        self.assertIn("RENDER_COMPRESSION_APPLIED", scene.warnings)

    def test_label_fallback_uses_leaders_or_callouts_for_thin_layers(self) -> None:
        profile = built_in_render_profile("illustrative_process_cross_section")
        scene = build_cross_section_scene(conformal_liner_result(), profile, materials=MATERIALS)

        liner_labels = [
            label for label in scene.labels
            if label.text.startswith("ALD Al2O3")
        ]

        self.assertTrue(liner_labels)
        self.assertTrue(
            any(label.placement_type in {"leader", "callout"} for label in liner_labels)
        )

    def test_scene_model_serializes_round_trip(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(simple_stack_result(), profile, materials=MATERIALS)

        loaded = scene_from_dict(scene_to_dict(scene))

        self.assertEqual(scene.render_mode_id, loaded.render_mode_id)
        self.assertEqual(len(scene.material_shapes), len(loaded.material_shapes))
        self.assertEqual(scene.labels[0].text, loaded.labels[0].text)

    def test_svg_backend_returns_export_result_without_png_dependency(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        scene = build_cross_section_scene(simple_stack_result(), profile, materials=MATERIALS)

        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "cross.svg"
            result = SvgCrossSectionRenderer().render(
                scene,
                CrossSectionOutputSpec(output_path=str(target), artifact_id="artifact-001"),
            )

        self.assertEqual("artifact-001", result.artifact_id)
        self.assertEqual("success", result.status)
        self.assertEqual(1200, result.width_px)
        self.assertEqual("engineering_dark", result.render_metadata["theme_id"])
        self.assertEqual("#0b1120", result.render_metadata["background_color"])

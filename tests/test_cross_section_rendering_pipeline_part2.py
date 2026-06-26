import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.rendering.cross_section import (
    CrossSectionOutputSpec,
    SvgCrossSectionRenderer,
    build_cross_section_scene,
    build_failed_render_warning,
    build_process_flow_scenes,
    build_render_artifact_record,
    built_in_render_profile,
)
from tests.cross_section_rendering_fixtures import (
    MATERIALS,
    fib_full_stack_result,
    process_flow_result,
    simple_stack_result,
)

if __name__ == "__main__":
    unittest.main()


class CrossSectionRenderingPipelineTestsPart2(unittest.TestCase):
    def test_point_stack_backend_uses_dark_schematic_not_lateral_cross_section(self) -> None:
        profile = built_in_render_profile("point_stack_schematic")
        scene = build_cross_section_scene(simple_stack_result(), profile, materials=MATERIALS)

        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "point-stack.svg"
            SvgCrossSectionRenderer().render(
                scene,
                CrossSectionOutputSpec(output_path=str(target), artifact_id="artifact-stack"),
            )
            svg = target.read_text(encoding="utf-8")

        self.assertIn("#0b1120", svg)
        self.assertIn("Ordered material stack at selected point", svg)
        self.assertIn("Lateral geometry hidden for point-stack view", svg)

    def test_artifact_record_and_failed_warning_store_render_metadata(self) -> None:
        profile = built_in_render_profile("fib_full_stack_compressed")
        scene = build_cross_section_scene(fib_full_stack_result(), profile, materials=MATERIALS)
        artifact = build_render_artifact_record(
            "capture",
            "cap-001",
            "full_stack_compressed_image",
            "full_stack_compressed_image",
            "process/full-stack.svg",
            scene,
        )
        warning = build_failed_render_warning("cap-001", artifact, "RENDER_EXPORT_FAILED",
                                              "Render export failed.")

        self.assertEqual("full_stack_compressed_image", artifact.type)
        self.assertEqual("fib_full_stack_compressed",
                         artifact.extensions["cross_section_render"]["render_mode_id"])
        self.assertTrue(artifact.extensions["cross_section_render"]["measurement_annotations"])
        self.assertIn("measurement_caption", artifact.extensions["report_summary"])
        self.assertEqual("RENDER_EXPORT_FAILED", warning.code)
        self.assertEqual((artifact.id,), warning.related_artifact_refs)

    def test_process_flow_frames_skip_unchanged_signatures_and_add_step_labels(self) -> None:
        profile = built_in_render_profile("process_flow_frame")
        scenes = build_process_flow_scenes(process_flow_result(), profile, materials=MATERIALS)

        self.assertEqual(3, len(scenes))
        self.assertTrue(all(scene.annotations for scene in scenes))
        self.assertEqual(
            {"01", "02", "04"},
            {scene.source_refs["selected_step_id"] for scene in scenes},
        )

    def test_missing_profile_id_raises_for_validation(self) -> None:
        with self.assertRaises(KeyError):
            built_in_render_profile("missing")

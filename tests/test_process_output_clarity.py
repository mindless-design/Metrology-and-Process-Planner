import unittest

from metrology_process_planner.rendering.cross_section import (
    CrossSectionRenderResult,
    build_render_artifact_record,
    built_in_render_profile,
    default_render_profile_id,
    resolve_render_profile,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.process_context import regenerate_process_outputs
from metrology_process_planner.workflows.process_context_models import (
    RegenerateProcessOutputsCommand,
)
from tests.process_output_fixtures import profile_session_with_recipe
from tests.test_synthetic_render_regression import _build_scene


class ProcessOutputClarityTests(unittest.TestCase):
    def test_mode_specific_render_profile_defaults_are_stable(self) -> None:
        self.assertEqual("profilometry_surface_profile", default_render_profile_id("line_profile"))
        self.assertEqual("point_stack_schematic", default_render_profile_id("point_stack"))
        self.assertEqual(
            "fib_full_stack_compressed",
            default_render_profile_id("full_stack_compressed_image"),
        )
        self.assertEqual("process_flow_frame", default_render_profile_id("process_flow_frame"))

    def test_missing_profile_resolution_warns_and_falls_back(self) -> None:
        resolution = resolve_render_profile("line_profile", "missing-profile")

        self.assertEqual("physical_cross_section", resolution.profile.profile_id)
        self.assertEqual(("RENDER_PROFILE_MISSING",), resolution.warnings)

    def test_render_simplification_policy_is_attached_to_profiles(self) -> None:
        profile = built_in_render_profile("profilometry_surface_profile")

        self.assertTrue(profile.simplification_policy.enabled)
        self.assertTrue(profile.simplification_policy.preserve_surface_profile)
        self.assertTrue(profile.simplification_policy.hide_irrelevant_buried_layers)

    def test_scene_records_simplification_metadata_without_solver_mutation(self) -> None:
        scene = _build_scene("profilometry_surface_recipe", "profilometry_surface_profile")

        self.assertIn("RENDER_SIMPLIFICATION_APPLIED", scene.warnings)
        annotations = tuple(
            item for item in scene.annotations if item.get("kind") == "render_simplification"
        )
        self.assertTrue(annotations)
        self.assertEqual(
            "profilometry_surface_profile",
            dict(scene.source_refs or {})["render_profile_id"],
        )

    def test_thin_layer_visibility_metadata_is_explicit(self) -> None:
        scene = _build_scene("conformal_liner_recipe", "illustrative_process_cross_section")

        self.assertIn("RENDER_THIN_LAYER_EXAGGERATED", scene.warnings)
        self.assertTrue(any(shape.exaggerated_flag for shape in scene.material_shapes))
        legend = scene.legend
        self.assertIsNotNone(legend)
        assert legend is not None
        self.assertTrue(legend.show_exaggeration_notes)

    def test_render_artifact_metadata_includes_profile_warnings_and_simplification(self) -> None:
        scene = _build_scene("fib_full_stack_recipe", "fib_full_stack_compressed")
        result = CrossSectionRenderResult(
            "artifact-fib",
            "tests/output/visual_polish_gallery/fib.svg",
            1200,
            720,
            "success",
            render_metadata={"backend": "svg"},
        )

        artifact = build_render_artifact_record(
            "capture",
            "cap-fib",
            "full_stack_compressed_image",
            "full_stack_compressed_image",
            "visual_polish_gallery/fib.svg",
            scene,
            result,
        )
        metadata = dict(artifact.extensions or {})["cross_section_render"]

        self.assertEqual("fib_full_stack_compressed", metadata["render_profile_id"])
        self.assertEqual("engineering_dark", metadata["theme_id"])
        self.assertEqual("#0b1120", metadata["background_color"])
        self.assertIn("RENDER_COMPRESSION_APPLIED", metadata["render_warnings"])
        self.assertTrue(metadata["simplification"])

    def test_process_output_editor_exposes_render_profile(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as folder:
            session = regenerate_process_outputs(
                profile_session_with_recipe(Path(folder)),
                RegenerateProcessOutputsCommand("cap-001"),
            ).session

        document = SessionDocumentBuilder().build(session)
        item = document.items_by_id["process_output:process-output-cap-001"]
        fields = DefaultSessionModeAdapter().metadata_fields(document.session, item)
        values = {field.key: field.value for field in fields}

        self.assertEqual("profilometry_surface_profile", values["render_profile_id"])

    def test_visual_polish_gallery_generator_outputs_expected_examples(self) -> None:
        from pathlib import Path

        from tools.generate_visual_polish_gallery import main

        main()
        output = Path("tests/output/visual_polish_gallery")

        self.assertTrue((output / "index.html").exists())
        self.assertTrue((output / "thin_conformal_liner.svg").exists())
        self.assertTrue((output / "fib_full_stack_compressed.scene.json").exists())
        self.assertTrue((output / "images" / "cap-001-site_overview_image.svg").exists())
        self.assertTrue((output / "images" / "images" / "cap-001.png").exists())
        self.assertIn(
            "#0b1120",
            (output / "ellipsometry_point_stack.svg").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()

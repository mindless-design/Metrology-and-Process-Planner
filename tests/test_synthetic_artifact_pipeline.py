import json
import unittest
from pathlib import Path

from metrology_process_planner.rendering.cross_section import (
    CrossSectionRenderResult,
    build_failed_render_warning,
    build_render_artifact_record,
    built_in_render_profile,
)
from tests.synthetic_process_lab import SESSION_ROOT
from tests.test_synthetic_render_regression import _build_scene


class SyntheticArtifactPipelineTests(unittest.TestCase):
    def test_cross_section_artifact_record_updates_registry_metadata(self) -> None:
        scene = _build_scene("fib_full_stack_recipe", "fib_full_stack_compressed")
        result = CrossSectionRenderResult(
            "artifact-fib",
            "tests/output/render_gallery/fib_full_stack.svg",
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
            "render_gallery/fib_full_stack.svg",
            scene,
            result,
        )

        self.assertEqual("present", artifact.status.value)
        self.assertEqual("fib_full_stack_compressed",
                         artifact.extensions["cross_section_render"]["render_mode_id"])

    def test_failed_render_creates_warning_without_crashing(self) -> None:
        scene = _build_scene("simple_stack_recipe", "physical_cross_section")
        result = CrossSectionRenderResult("artifact-failed", "", 0, 0, "failed")
        artifact = build_render_artifact_record(
            "capture", "cap-001", "site_image", "site_image", "", scene, result
        )

        warning = build_failed_render_warning(
            "cap-001", artifact, "RENDER_BACKEND_UNAVAILABLE", "Render backend unavailable."
        )

        self.assertEqual("failed", artifact.status.value)
        self.assertEqual("RENDER_BACKEND_UNAVAILABLE", warning.code)

    def test_synthetic_sessions_cover_expected_modes_and_artifact_intents(self) -> None:
        session_paths = sorted(SESSION_ROOT.glob("*_session/session.json"))
        modes = {_load(path)["mode"] for path in session_paths}
        artifact_roles = {
            role
            for path in session_paths
            for role in _load(path).get("metadata", {}).get("artifacts", {})
        }

        self.assertIn("simple_capture", modes)
        self.assertIn("fib_planning", modes)
        self.assertIn("grid_capture", modes)
        self.assertIn("full_stack_compressed", artifact_roles)
        self.assertIn("process_flow_frames", artifact_roles)

    def test_broken_sessions_advertise_repair_diagnostic_targets(self) -> None:
        expected = {
            "ARTIFACT_MISSING",
            "RECIPE_MISSING",
            "GEOMETRY_LAYER_MISSING",
            "ARTIFACT_STALE",
            "MEASUREMENT_INVALID",
            "MODE_INVALID",
        }
        actual = {
            _load(path)["metadata"]["expected_warning"]
            for path in (SESSION_ROOT / "broken").glob("*.json")
        }

        self.assertEqual(expected, actual)

    def test_missing_recipe_fixture_is_warning_condition(self) -> None:
        payload = _load(SESSION_ROOT / "broken" / "missing_recipe_session.json")
        recipe_path = (SESSION_ROOT / payload["metadata"]["recipe"]).resolve()

        self.assertFalse(recipe_path.exists())
        self.assertEqual("RECIPE_MISSING", payload["metadata"]["expected_warning"])

    def test_render_profiles_needed_by_artifact_pipeline_exist(self) -> None:
        for profile_id in (
            "physical_cross_section",
            "illustrative_process_cross_section",
            "profilometry_surface_profile",
            "fib_full_stack_compressed",
            "process_flow_frame",
            "point_stack_schematic",
        ):
            self.assertEqual(profile_id, built_in_render_profile(profile_id).profile_id)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


if __name__ == "__main__":
    unittest.main()

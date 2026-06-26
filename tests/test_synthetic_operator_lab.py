import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus
from tests.synthetic_operator_lab import (
    run_changed_geometry_scan,
    run_happy_path,
    run_missing_recipe_path,
    run_missing_source_artifact,
)
from tests.synthetic_operator_lab_summaries import write_failure_debug
from tests.synthetic_process_lab import GOLDEN_ROOT

GOLDEN = GOLDEN_ROOT / "operator_lab"


class SyntheticOperatorLabTests(unittest.TestCase):
    def test_happy_path_builds_complete_operator_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_happy_path(Path(temp_dir) / "happy")

            self._assert_matches_golden("happy_path.expected.json", result.summary)
            self.assertTrue(result.paths.session_json.exists())
            self.assertTrue(result.gallery_manifest_path and result.gallery_manifest_path.exists())
            self.assertIn("artifact_gallery", result.report_sections)
            self.assertTrue(
                any(item["status"] == "present" for item in result.summary["render_scenes"])
            )
            self.assertTrue(result.summary["reports"])

    def test_missing_recipe_path_keeps_session_valid_with_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_missing_recipe_path(Path(temp_dir) / "missing_recipe")

            self._assert_matches_golden("missing_recipe.expected.json", result.summary)
            self.assertTrue(result.paths.session_json.exists())
            self.assertEqual(
                {"pending_solver"},
                {item.status for item in result.session.process_outputs},
            )
            self.assertTrue(
                all(
                    artifact.status is ArtifactStatus.PLACEHOLDER
                    for artifact in result.session.artifacts.values()
                )
            )

    def test_missing_source_artifact_diagnostics_and_report_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_missing_source_artifact(Path(temp_dir) / "missing_source")

            self._assert_matches_golden("missing_source_artifact.expected.json", result.summary)
            self.assertIn("artifact_gallery", result.report_sections)
            source = result.session.artifacts["source-site-image"]
            self.assertEqual(ArtifactStatus.MISSING, source.status)
            self.assertEqual("regenerate_artifact", source.repair.repair_action)
            self.assertTrue(source.warning_ids)

    def test_changed_capture_geometry_marks_report_outputs_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_changed_geometry_scan(Path(temp_dir) / "changed_geometry")

            self._assert_matches_golden("changed_geometry.expected.json", result.summary)
            stale = [
                artifact.id
                for artifact in result.session.artifacts.values()
                if artifact.status is ArtifactStatus.STALE
            ]
            self.assertTrue(stale)

    def _assert_matches_golden(self, name: str, actual: dict[str, object]) -> None:
        expected_path = GOLDEN / name
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        if actual != expected:
            write_failure_debug(expected_path.stem, actual)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.app.diagnostics_summary import diagnostics_summary_rows
from metrology_process_planner.domains.session import (
    SessionMode,
    built_in_mode_registry,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from tests.editor_render_fixtures import (
    session_without_pending,
)

if __name__ == "__main__":
    unittest.main()


class NonProcessModeHardeningTestsPart3(unittest.TestCase):
    def test_capture_csv_includes_recipe_free_review_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "captures.csv"
            source = session_without_pending()

            CaptureCsvExporter().export(source, destination)

            text = destination.read_text(encoding="utf-8")
        self.assertIn("sequence", text.splitlines()[0])
        self.assertIn("center_x", text.splitlines()[0])
        self.assertIn("measurement_ids", text.splitlines()[0])
        self.assertIn("artifact_statuses", text.splitlines()[0])
        self.assertIn("meas-001", text)
        self.assertIn("crop:present", text)

    def test_advanced_diagnostics_confirms_recipe_free_mode_policy(self) -> None:
        rows = dict(
            diagnostics_summary_rows(
                session_without_pending(),
                (),
                built_in_mode_registry(),
            )
        )

        self.assertEqual("false", rows["Mode Process Aware"])
        self.assertIn("simple_capture (Simple Labeled Capture", rows["Loaded Mode Definition"])
        self.assertEqual("false", rows["Recipe Required"])
        self.assertEqual("none", rows["Solver Operation"])
        self.assertEqual("false", rows["Process Context Visible"])
        self.assertEqual("not_required", rows["Setup State"])

    def test_process_aware_modes_explicitly_show_process_context(self) -> None:
        registry = built_in_mode_registry()
        definition = registry.definition(SessionMode.PROFILOMETRY_PLANNER.value)

        self.assertTrue(definition.editor.process_context_visible)

import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import SessionMode, built_in_mode_registry
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.mode_capture_defaults import capture_defaults
from tests.editor_render_fixtures import session


class CdsemMeasurementModeAliasTests(unittest.TestCase):
    def test_cdsem_measurement_is_registered_as_recipe_free_mode(self) -> None:
        definition = built_in_mode_registry().definition(SessionMode.CDSEM_MEASUREMENT.value)

        self.assertEqual("cdsem_measurement", definition.mode_id)
        self.assertEqual("forbidden", definition.process.recipe_policy)
        self.assertEqual("none", definition.process.solver_operation)
        self.assertFalse(definition.capabilities.supports_process_solver)
        self.assertFalse(definition.editor.process_context_visible)
        self.assertIn("required_sem_alignment_mark", definition.setup.stage_types)

    def test_legacy_cdsem_capture_mode_remains_registered(self) -> None:
        registry = built_in_mode_registry()

        self.assertIn(SessionMode.CDSEM_CAPTURE.value, registry.mode_ids())
        self.assertIn(SessionMode.CDSEM_MEASUREMENT.value, registry.mode_ids())

    def test_cdsem_planning_alias_is_registered_but_hidden(self) -> None:
        registry = built_in_mode_registry()
        definition = registry.definition(SessionMode.CDSEM_PLANNING.value)

        self.assertIn(SessionMode.CDSEM_PLANNING.value, registry.mode_ids())
        self.assertNotIn(SessionMode.CDSEM_PLANNING.value, registry.visible_mode_ids())
        self.assertEqual("forbidden", definition.process.recipe_policy)
        self.assertEqual("none", definition.process.solver_operation)
        self.assertFalse(definition.capabilities.supports_process_solver)
        self.assertFalse(definition.editor.process_context_visible)
        self.assertIn("required_sem_alignment_mark", definition.setup.stage_types)

    def test_cdsem_measurement_defaults_match_cdsem_site_capture(self) -> None:
        current = session()
        pending = current.pending_captures[0]
        current = replace(current, mode=SessionMode.CDSEM_MEASUREMENT)

        metadata = capture_defaults(current, pending, "cap-001", "")

        self.assertEqual("cdsem_site", metadata.role)
        self.assertEqual("cdsem_site", metadata.capture_type)

    def test_cdsem_planning_defaults_match_cdsem_site_capture(self) -> None:
        current = session()
        pending = current.pending_captures[0]
        current = replace(current, mode=SessionMode.CDSEM_PLANNING)

        metadata = capture_defaults(current, pending, "cap-001", "")

        self.assertEqual("cdsem_site", metadata.role)
        self.assertEqual("cdsem_site", metadata.capture_type)

    def test_cdsem_measurement_csv_exports_feature_type_metadata(self) -> None:
        capture = replace(
            session().captures[0],
            metadata={"feature_type": "line_space", "label": "CDSEM Site 001"},
        )
        source = replace(
            session(),
            mode=SessionMode.CDSEM_MEASUREMENT,
            captures=(capture,),
        )

        row = CaptureCsvExporter().rows_for_session(source)[0]

        self.assertEqual("line_space", row["feature_type"])

    def test_cdsem_measurement_csv_exports_capture_level_measurement_plan(self) -> None:
        capture = replace(
            session().captures[0],
            measurements=(),
            metadata={
                "measurement_type": "space_cd",
                "target": "28.0",
                "lsl": "26.0",
                "usl": "30.0",
                "edge_convention": "inner_edges",
            },
        )
        source = replace(
            session(),
            mode=SessionMode.CDSEM_MEASUREMENT,
            captures=(capture,),
        )

        row = CaptureCsvExporter().rows_for_session(source)[0]

        self.assertEqual("space_cd", row["measurement_type"])
        self.assertEqual("28.0", row["target"])
        self.assertEqual("26.0", row["lsl"])
        self.assertEqual("30.0", row["usl"])
        self.assertEqual("inner_edges", row["edge_convention"])

    def test_copy_csv_row_uses_canonical_cdsem_export_columns(self) -> None:
        capture = replace(
            session().captures[0],
            measurements=(),
            metadata={
                "feature_type": "line_space",
                "measurement_type": "space_cd",
                "target": "28.0",
                "lsl": "26.0",
                "usl": "30.0",
                "edge_convention": "inner_edges",
            },
        )
        source = replace(
            session(),
            mode=SessionMode.CDSEM_MEASUREMENT,
            captures=(capture,),
        )
        document = SessionDocumentBuilder().build(source)

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.COPY_CSV_ROW, "Copy CSV Row", "capture:cap-001"),
        )

        self.assertEqual("success", result.status)
        self.assertIn("line_space", result.message)
        self.assertIn("space_cd", result.message)
        self.assertIn("inner_edges", result.message)

    def test_cdsem_planning_uses_metrology_report_template(self) -> None:
        template = built_in_report_templates()["metrology_report"]

        self.assertTrue(template.supports_mode(SessionMode.CDSEM_PLANNING.value))


if __name__ == "__main__":
    unittest.main()

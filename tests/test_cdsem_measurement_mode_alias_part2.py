import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session


class CdsemMeasurementModeAliasTestsPart2(unittest.TestCase):
    def test_cdsem_measurement_csv_exports_feature_type_metadata(self) -> None:
        capture = replace(
            session().captures[0],
            metadata={"feature_type": "line_space", "label": "CDSEM Site 001"},
        )
        source = replace(session(), mode=SessionMode.CDSEM_MEASUREMENT, captures=(capture,))

        row = CaptureCsvExporter().rows_for_session(source)[0]

        self.assertEqual("line_space", row["feature_type"])

    def test_cdsem_measurement_csv_exports_capture_level_measurement_plan(self) -> None:
        row = _row_for_mode(SessionMode.CDSEM_MEASUREMENT)

        self.assertEqual("space_cd", row["measurement_type"])
        self.assertEqual("28.0", row["target"])
        self.assertEqual("26.0", row["lsl"])
        self.assertEqual("30.0", row["usl"])
        self.assertEqual("inner_edges", row["edge_convention"])

    def test_cdsem_planning_csv_exports_capture_level_measurement_plan(self) -> None:
        row = _row_for_mode(SessionMode.CDSEM_PLANNING)

        self.assertEqual("line_space", row["feature_type"])
        self.assertEqual("space_cd", row["measurement_type"])
        self.assertEqual("28.0", row["target"])
        self.assertEqual("26.0", row["lsl"])
        self.assertEqual("30.0", row["usl"])
        self.assertEqual("inner_edges", row["edge_convention"])

    def test_copy_csv_row_uses_canonical_cdsem_export_columns(self) -> None:
        result = _copy_row_for_mode(SessionMode.CDSEM_MEASUREMENT)

        self.assertEqual("success", result.status)
        self.assertIn("line_space", result.message)
        self.assertIn("space_cd", result.message)
        self.assertIn("inner_edges", result.message)

    def test_cdsem_planning_copy_csv_row_uses_canonical_cdsem_export_columns(self) -> None:
        result = _copy_row_for_mode(SessionMode.CDSEM_PLANNING)

        self.assertEqual("success", result.status)
        self.assertIn("line_space", result.message)
        self.assertIn("space_cd", result.message)
        self.assertIn("inner_edges", result.message)

    def test_cdsem_planning_uses_metrology_report_template(self) -> None:
        template = built_in_report_templates()["metrology_report"]

        self.assertTrue(template.supports_mode(SessionMode.CDSEM_PLANNING.value))


def _row_for_mode(mode: SessionMode):
    return CaptureCsvExporter().rows_for_session(_source_for_mode(mode))[0]


def _copy_row_for_mode(mode: SessionMode):
    document = SessionDocumentBuilder().build(_source_for_mode(mode))
    return EditorActionDispatcher().dispatch(
        document,
        EditorAction(EditorActionType.COPY_CSV_ROW, "Copy CSV Row", "capture:cap-001"),
    )


def _source_for_mode(mode: SessionMode):
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
    return replace(session(), mode=mode, captures=(capture,))


if __name__ == "__main__":
    unittest.main()

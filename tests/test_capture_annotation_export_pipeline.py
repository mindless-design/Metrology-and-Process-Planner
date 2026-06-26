import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import SessionMode, WarningRecord
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.rendering import build_layout_annotation_scene
from metrology_process_planner.rendering.primitives import LineMark
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.measurement_workflow import save_pending_measurements
from tests.capture_metadata_pipeline_fixtures import (
    line_feature_capture,
    session_with_capture,
    simple_capture,
)
from tests.measurement_child_fixtures import (
    document_with_pending_measurement,
    saved_capture_session,
    saved_measurement_document,
)


class CaptureAnnotationExportPipelineTests(unittest.TestCase):
    def test_feature_annotations_are_added_to_layout_scene(self) -> None:
        scene = build_layout_annotation_scene(line_feature_capture())
        line_marks = [
            primitive for primitive in scene.primitives if isinstance(primitive, LineMark)
        ]

        self.assertGreaterEqual(len(line_marks), 2)
        self.assertTrue(any(mark.label == "Profile Line" for mark in line_marks))

    def test_csv_exports_geometry_feature_measurement_and_artifacts(self) -> None:
        row = CaptureCsvExporter().rows_for_session(
            session_with_capture(line_feature_capture()),
        )[0]

        self.assertEqual(5, row["center_x"])
        self.assertEqual(10, row["width"])
        self.assertEqual("feat-001", row["feature_id"])
        self.assertEqual(5, row["feature_midpoint_x"])
        self.assertEqual("meas-001", row["measurement_id"])
        self.assertEqual("capture-cap-001-site_image", row["site_image_artifact_id"])
        self.assertEqual("capture-cap-001-line_annotation", row["annotation_artifact_id"])
        self.assertEqual("layout.gds", row["source_layout_file"])

    def test_csv_exports_saved_measurement_metadata_and_artifact_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)

        row = CaptureCsvExporter().rows_for_session(document.session)[0]

        self.assertEqual("cd", row["measurement_type"])
        self.assertEqual(
            "measurement-meas-001-measurement_annotation_svg",
            row["measurement_artifact_id"],
        )
        self.assertEqual("present", row["measurement_artifact_status"])
        self.assertIn("meas-001", row["measurement_ids"])

    def test_csv_warning_count_includes_nested_measurement_artifact_warning(self) -> None:
        document = document_with_pending_measurement(saved_capture_session())
        saved = save_pending_measurements(document.session)

        row = CaptureCsvExporter().rows_for_session(saved)[0]

        self.assertEqual("pending", row["measurement_artifact_status"])
        self.assertEqual(1, row["warning_count"])

    def test_csv_warning_count_hides_process_warning_for_recipe_free_mode(self) -> None:
        session = saved_capture_session()
        capture = replace(session.captures[0], warning_ids=("process-warning", "capture-warning"))
        session = replace(
            session,
            captures=(capture,),
            warnings=(
                WarningRecord(
                    id="process-warning",
                    message="Recipe missing",
                    source="process_context",
                    code="PROCESS_RECIPE_FILE_NOT_FOUND",
                ),
                WarningRecord(id="capture-warning", message="Capture artifact missing"),
            ),
        )

        row = CaptureCsvExporter().rows_for_session(session)[0]

        self.assertEqual(SessionMode.SIMPLE_CAPTURE.value, row["session_mode"])
        self.assertEqual(1, row["warning_count"])

    def test_editor_metadata_and_copy_actions_include_geometry(self) -> None:
        document = SessionDocumentBuilder().build(session_with_capture(simple_capture()))
        item = document.items_by_id["capture:cap-001"]
        adapter = DefaultSessionModeAdapter()

        fields = adapter.metadata_fields(document.session, item)
        actions = adapter.actions(document.session, item)

        self.assertTrue(
            any(field.key == "center" and field.value == "5.0, 5.0" for field in fields)
        )
        self.assertTrue(any(field.key == "bounds" for field in fields))
        self.assertTrue(any(action.label == "Copy Center Coordinate" for action in actions))
        self.assertTrue(any(action.label == "Copy Bounds" for action in actions))


if __name__ == "__main__":
    unittest.main()

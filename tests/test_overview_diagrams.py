import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.rendering.overview import (
    UserLabelRecord,
    build_label_content,
    build_overview_scene,
    extract_label_targets,
    generate_overview_artifact,
    scene_to_dict,
    user_labels_from_session,
    with_user_label,
)
from metrology_process_planner.reporting.builder import ReportModelBuilder
from metrology_process_planner.reporting.templates import ReportTemplate
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


class OverviewDiagramTests(unittest.TestCase):
    def test_label_target_extraction_from_captures_measurements_and_user_labels(self) -> None:
        source = with_user_label(_session(), _user_label())

        targets = extract_label_targets(source)

        target_types = {target.target_type for target in targets}
        self.assertIn("capture_box", target_types)
        self.assertIn("measurement_line", target_types)
        self.assertIn("user_box", target_types)

    def test_user_labels_round_trip_through_session_json_extensions(self) -> None:
        source = with_user_label(_session(), _user_label())

        restored = SessionRecord.from_dict(source.to_dict())

        labels = user_labels_from_session(restored)
        self.assertEqual(1, len(labels))
        self.assertEqual("Check alignment here", labels[0].title)

    def test_outside_edge_placement_has_no_label_collisions_for_simple_scene(self) -> None:
        scene = build_overview_scene(_session(capture_count=3))

        self.assertGreaterEqual(scene.placement_metadata.labels_placed, 3)
        self.assertEqual(0, scene.placement_metadata.unresolved_collisions)
        self.assertEqual(scene.placement_metadata.labels_placed, len(scene.leader_paths))

    def test_crowded_placement_emits_warning_for_unresolved_layout(self) -> None:
        request = None
        source = _session(capture_count=30)

        scene = build_overview_scene(source, request)

        self.assertGreaterEqual(scene.placement_metadata.labels_requested, 30)
        self.assertTrue(
            "LABEL_LAYOUT_COLLISION_UNRESOLVED" in scene.warnings
            or "LABELS_OMITTED_DUE_TO_SPACE" in scene.warnings
        )

    def test_label_content_generation_uses_mode_neutral_roles(self) -> None:
        targets = extract_label_targets(_session())

        content = build_label_content(targets, "detailed")

        self.assertTrue(any(item.title.startswith("Site") for item in content))
        self.assertTrue(any(item.title == "Gate CD" for item in content))

    def test_overview_artifact_record_is_created_and_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()

            updated = generate_overview_artifact(_session(), paths.folder)

            artifacts = updated.artifacts
            assert artifacts is not None
            artifact = next(iter(artifacts.values()))
            extensions = artifact.extensions
            assert extensions is not None
            self.assertEqual("session_overview_image", artifact.type)
            self.assertTrue((paths.folder / artifact.relative_path).exists())
            self.assertEqual(
                "scene-session-001-session_overview",
                extensions["diagram_scene_id"],
            )
            report_summary = extensions["report_summary"]
            self.assertEqual(2, report_summary["labels_requested"])
            self.assertEqual(report_summary["labels_placed"], report_summary["leader_count"])

    def test_editor_dispatcher_generates_session_overview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = SessionDocumentBuilder().build(_session())

            result = EditorActionDispatcher(paths=paths).dispatch(
                document,
                EditorAction(EditorActionType.GENERATE_SESSION_OVERVIEW, "Generate", "dashboard"),
            )

            self.assertEqual("success", result.status)
            self.assertIn("overview:session_overview", result.document.items_by_id)

    def test_report_section_prefers_overview_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            session = generate_overview_artifact(_session(), paths.folder)
            document = SessionDocumentBuilder().build(session)
            template = ReportTemplate("overview", "Overview", ("session_overview",))

            report = ReportModelBuilder().build(document, template)

            self.assertEqual("session_overview", report.sections[0].section_id)
            self.assertFalse(report.sections[0].figures[0].placeholder)
            self.assertIn("Labels: ", report.sections[0].body[0])
            self.assertIn("labels placed", report.sections[0].figures[0].notes)

    def test_missing_report_overview_uses_placeholder(self) -> None:
        document = ReportModelBuilder().build(
            SessionDocumentBuilder().build(_session()),
            ReportTemplate("overview", "Overview", ("session_overview",)),
        )

        figure = document.sections[0].figures[0]
        self.assertTrue(figure.placeholder)
        self.assertEqual("", figure.artifact_id)
        self.assertEqual(("Overview artifact is missing.",), document.sections[0].body)
    def test_scene_json_contains_layout_metadata(self) -> None:
        scene = build_overview_scene(_session())
        data = scene_to_dict(scene)
        self.assertEqual("outside_edge_callouts", data["placement_metadata"]["strategy_used"])


def _session(capture_count: int = 1) -> SessionRecord:
    captures = tuple(_capture(index) for index in range(1, capture_count + 1))
    return SessionRecord(
        "session-001",
        "Overview Demo",
        SessionMode.SIMPLE_CAPTURE,
        "2026-06-24T00:00:00Z",
        "2026-06-24T00:00:00Z",
        captures=captures,
    )

def _capture(index: int) -> CaptureRecord:
    left = float(index * 20)
    measurement = MeasurementRecord(
        f"meas-{index:03d}",
        "Gate CD",
        Point(left + 1, 1),
        Point(left + 8, 1),
        target=6.0,
    )
    return CaptureRecord(
        f"cap-{index:03d}",
        f"Gate array {index}",
        CaptureGeometry.box(Box(left, 0, left + 10, 10)),
        "2026-06-24T00:00:00Z",
        sequence=index,
        measurements=(measurement,) if index == 1 else (),
    )

def _user_label() -> UserLabelRecord:
    return UserLabelRecord(
        "user-001",
        {"kind": "box", "bounds": Box(50, 20, 70, 35).to_dict()},
        "Check alignment here",
    )

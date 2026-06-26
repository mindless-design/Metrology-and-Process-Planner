import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    CanvasObjectType,
    CaptureGeometry,
    CaptureRecord,
    ModeDefinition,
    ModeRegistry,
    PendingCapture,
    ReportRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows.canvas_interaction_models import InteractionContext
from metrology_process_planner.workflows.editor import (
    SessionDocumentBuilder,
    mark_metadata_edit,
)
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService


def _measurement() -> MeasurementRecord:
    return MeasurementRecord(
        "meas-001",
        "Gate CD",
        Point(1, 1),
        Point(3, 1),
        target=2.0,
        lower_spec_limit=1.8,
        upper_spec_limit=2.2,
    )


def _capture() -> CaptureRecord:
    return CaptureRecord(
        "cap-001",
        "Site 7",
        CaptureGeometry.box(Box(0, 0, 5, 5)),
        "2026-06-24T00:00:00Z",
        sequence=7,
        measurements=(_measurement(),),
    )


def _artifacts() -> dict[str, ArtifactRecord]:
    return {
        "site-image": ArtifactRecord(
            "site-image",
            "image",
            "Labeled Site Image",
            "images/site.png",
            ArtifactOwnerRef("capture", "cap-001", "site_image_labeled"),
        ),
        "measurement-annotation": ArtifactRecord(
            "measurement-annotation",
            "image",
            "Measurement Annotation",
            "images/measurement.png",
            ArtifactOwnerRef("measurement", "meas-001", "measurement_annotation_image"),
        ),
        "summary-csv": ArtifactRecord(
            "summary-csv",
            "csv",
            "Capture CSV",
            "exports/session_summary.csv",
            ArtifactOwnerRef("session", "session-001", "csv"),
            dependencies=(ArtifactDependencyRef(kind="capture", id="cap-001"),),
        ),
        "pptx-report": ArtifactRecord(
            "pptx-report",
            "pptx",
            "PowerPoint Report",
            "reports/session_report.pptx",
            ArtifactOwnerRef("report", "report-001", "pptx"),
            dependencies=(ArtifactDependencyRef(kind="capture", id="cap-001"),),
        ),
    }


def _session() -> SessionRecord:
    return SessionRecord(
        "session-001",
        "Editable Session",
        SessionMode.SIMPLE_CAPTURE,
        "2026-06-24T00:00:00Z",
        "2026-06-24T00:00:00Z",
        captures=(_capture(),),
        reports=(
            ReportRecord(
                "report-001",
                "Session Report",
                "pptx",
                artifact_refs={"pptx": "pptx-report"},
            ),
        ),
        artifacts=_artifacts(),
    )

def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class SessionEditingWorkflowTestsPart4(unittest.TestCase):
    def test_measurement_metadata_edit_marks_measurement_csv_and_report_stale(self) -> None:
        document = SessionDocumentBuilder().build(_session())

        edited = mark_metadata_edit(document, "measurement:meas-001", "target", "2.4")

        self.assertTrue(edited.dirty_state.is_dirty)
        self.assertEqual(
            ArtifactStatus.STALE,
            edited.session.artifacts["measurement-annotation"].status,
        )
        self.assertEqual(ArtifactStatus.STALE, edited.session.artifacts["summary-csv"].status)
        self.assertEqual("stale", edited.session.reports[0].status)

    def test_promoting_new_capture_stales_existing_exports_without_reusing_sequence(self) -> None:
        pending = PendingCapture(
            "pending-001",
            "session-001",
            "canvas-pending",
            object_type=CanvasObjectType.SITE_BOX,
            geometry=CaptureGeometry.box(Box(10, 10, 20, 20)),
        )
        session = replace(_session(), pending_captures=(pending,))

        result = PendingCaptureReviewService().save_pending_box(
            session,
            InteractionContext(),
            "pending-001",
        )

        self.assertTrue(result.handled)
        self.assertEqual((7, 8), tuple(capture.sequence for capture in result.session.captures))
        self.assertEqual("cap-008", result.session.captures[-1].id)
        self.assertEqual(ArtifactStatus.STALE, result.session.artifacts["summary-csv"].status)
        self.assertEqual(ArtifactStatus.STALE, result.session.artifacts["pptx-report"].status)

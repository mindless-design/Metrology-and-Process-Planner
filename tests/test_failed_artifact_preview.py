import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.artifact_helpers import capture_crop_artifact


class FailedArtifactPreviewTests(unittest.TestCase):
    def test_failed_artifact_becomes_repairable_placeholder_preview(self) -> None:
        failed_artifact = replace(
            capture_crop_artifact(width_px=0, height_px=0),
            status=ArtifactStatus.FAILED,
            repair=ArtifactRepairMetadata(
                repair_action="Regenerate Image",
                repair_suggestion="Regenerate the failed crop.",
            ),
        )
        document = SessionDocumentBuilder().build(_session(failed_artifact))
        capture = document.items_by_id["capture:cap-001"]
        previews = DefaultSessionModeAdapter().preview_options(document.session, capture)

        self.assertEqual("failed", capture.artifact_refs[0].status)
        self.assertEqual("failed", previews[0].status)
        self.assertIn("Failed artifact", previews[0].placeholder)
        self.assertIn("Belongs to capture-cap-001-crop (crop)", previews[0].placeholder)
        self.assertIn("CSV export can continue", previews[0].placeholder)
        self.assertIn("reports may use this placeholder", previews[0].placeholder)
        self.assertIn("Regenerate the failed crop.", previews[0].placeholder)
        self.assertEqual("Regenerate Image", previews[0].repair_action)

    def test_pending_artifact_becomes_status_placeholder_preview(self) -> None:
        pending_artifact = replace(
            capture_crop_artifact(),
            status=ArtifactStatus.PENDING,
            repair=ArtifactRepairMetadata(
                repair_action="Regenerate Image",
                repair_suggestion="Wait for capture image generation or regenerate it.",
            ),
        )
        document = SessionDocumentBuilder().build(_session(pending_artifact))
        capture = document.items_by_id["capture:cap-001"]
        previews = DefaultSessionModeAdapter().preview_options(document.session, capture)

        self.assertEqual("pending", capture.artifact_refs[0].status)
        self.assertEqual("pending", previews[0].status)
        self.assertIn("Pending artifact", previews[0].placeholder)
        self.assertIn("Belongs to capture-cap-001-crop (crop)", previews[0].placeholder)
        self.assertIn("CSV export can continue", previews[0].placeholder)
        self.assertIn("reports may use this placeholder", previews[0].placeholder)
        self.assertIn("Wait for capture image generation", previews[0].placeholder)
        self.assertEqual("Regenerate Image", previews[0].repair_action)


def _session(failed_artifact: ArtifactRecord) -> SessionRecord:
    capture = CaptureRecord(
        id="cap-001",
        label="Site 1",
        geometry=CaptureGeometry.box(Box(0, 0, 5, 5)),
        created_at="2026-06-23T20:00:00Z",
    )
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-23T20:00:00Z",
        updated_at="2026-06-23T20:00:00Z",
        captures=(capture,),
        artifacts={"capture-cap-001-crop": failed_artifact},
    )


if __name__ == "__main__":
    unittest.main()

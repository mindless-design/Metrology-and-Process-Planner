import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    DrawingOwnerRef,
    RenderRefreshRequest,
    RenderTarget,
    SessionDocumentBuilder,
    SessionRenderBridge,
)
from tests.editor_render_fixtures import FailingDrawingStore, session_without_pending


class EditorRenderBridgeRepairPreviewTests(unittest.TestCase):
    def test_repeated_measurement_annotation_failure_updates_repair_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = RenderRefreshRequest(
                targets=(
                    RenderTarget(
                        DrawingOwnerRef("measurement", "meas-001"),
                        "measurement_annotation",
                    ),
                )
            )
            bridge = SessionRenderBridge(
                SessionPaths.for_folder(Path(temp_dir)),
                drawing_store=FailingDrawingStore(),
            )
            first = bridge.refresh(session_without_pending(), target)
            second = bridge.refresh(first.session, target)

        artifact_id = "measurement-meas-001-measurement_annotation_svg"
        artifact = second.session.artifacts[artifact_id]
        document = SessionDocumentBuilder().build(second.session)
        previews = DefaultSessionModeAdapter().preview_options(
            document.session,
            document.items_by_id["measurement:meas-001"],
        )

        self.assertEqual(1, len(second.session.warnings))
        self.assertEqual(ArtifactStatus.FAILED, artifact.status)
        self.assertEqual("regenerate_artifact", artifact.repair.repair_action)
        self.assertIn("disk full", artifact.repair.last_error)
        self.assertEqual(
            ("render-measurement-meas-001-measurement_annotation-export",),
            artifact.warning_ids,
        )
        self.assertEqual("failed", previews[0].status)
        self.assertIn("disk full", previews[0].placeholder)
        self.assertIn(
            "Belongs to measurement meas-001",
            previews[0].placeholder,
        )
        self.assertIn("CSV export can continue", previews[0].placeholder)
        self.assertIn("Regenerate the artifact from the session editor.", previews[0].placeholder)
        self.assertEqual("regenerate_artifact", previews[0].repair_action)


if __name__ == "__main__":
    unittest.main()

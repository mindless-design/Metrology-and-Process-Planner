import unittest

from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.workflows import InteractionContext
from metrology_process_planner.workflows.pending_capture_review import PendingCaptureReviewService
from tests.test_non_process_capture_defaults import _pending_session


class NonProcessPlaceholderArtifactTests(unittest.TestCase):
    def test_pending_save_creates_site_image_placeholder_when_image_path_is_missing(self) -> None:
        source = _pending_session(SessionMode.SIMPLE_CAPTURE)

        result = PendingCaptureReviewService().save_pending_box(
            source,
            InteractionContext(),
            "pending-001",
            label="Missing image capture",
        )

        capture = result.session.captures[0]
        artifact_id = capture.artifact_refs["site_image"]
        artifact = result.session.artifacts[artifact_id]
        self.assertEqual("placeholder", artifact.status.value)
        self.assertEqual("site_image", artifact.owner.role)
        self.assertEqual((artifact.warning_ids[0],), capture.warning_ids)
        self.assertTrue(
            any(warning.code == "ARTIFACT_MISSING" for warning in result.session.warnings)
        )


if __name__ == "__main__":
    unittest.main()

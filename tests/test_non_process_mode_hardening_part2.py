import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    SessionMode,
    SetupState,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import (
    session,
    session_without_box_bounds,
    session_without_pending,
)

if __name__ == "__main__":
    unittest.main()


class NonProcessModeHardeningTestsPart2(unittest.TestCase):
    def test_capture_visual_regenerate_actions_match_existing_artifact_roles(self) -> None:
        source = replace(
            session_without_pending(),
            artifacts={
                "capture-cap-001-site_image_labeled": ArtifactRecord(
                    "capture-cap-001-site_image_labeled",
                    "image",
                    "Labeled site image",
                    "images/cap-001-labeled.svg",
                    ArtifactOwnerRef("capture", "cap-001", "site_image_labeled"),
                    status=ArtifactStatus.PRESENT,
                ),
            },
        )
        document = SessionDocumentBuilder().build(source)
        capture = document.items_by_id["capture:cap-001"]

        actions = DefaultSessionModeAdapter().actions(source, capture)
        labels = {action.label for action in actions}

        self.assertIn("Regenerate Labeled Site Image", labels)
        self.assertIn("Regenerate Visual Artifacts", labels)
        self.assertNotIn("Regenerate Site Overview", labels)
        self.assertNotIn("Regenerate Annotation Image", labels)

    def test_add_measurement_requires_saved_box_parent_canvas(self) -> None:
        source = session_without_box_bounds()
        document = SessionDocumentBuilder().build(source)
        adapter = DefaultSessionModeAdapter()
        capture = document.items_by_id["capture:cap-001"]
        actions = {action.label: action for action in adapter.actions(source, capture)}

        self.assertFalse(actions["Add Measurement"].enabled)
        self.assertEqual(
            "Measurements require a saved box capture.",
            actions["Add Measurement"].disabled_reason,
        )

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.ADD_MEASUREMENT, "Add Measurement", "capture:cap-001"),
        )

        self.assertEqual("blocked", result.status)
        self.assertIn("saved box capture", result.message)

    def test_add_measurement_reports_missing_canvas_parent_precisely(self) -> None:
        source = replace(session_without_pending(), canvas_objects=())
        document = SessionDocumentBuilder().build(source)
        adapter = DefaultSessionModeAdapter()
        capture = document.items_by_id["capture:cap-001"]
        actions = {action.label: action for action in adapter.actions(source, capture)}

        self.assertFalse(actions["Add Measurement"].enabled)
        self.assertEqual(
            "Measurements require a saved canvas box for this capture.",
            actions["Add Measurement"].disabled_reason,
        )

        result = EditorActionDispatcher().dispatch(
            document,
            EditorAction(EditorActionType.ADD_MEASUREMENT, "Add Measurement", "capture:cap-001"),
        )

        self.assertEqual("blocked", result.status)
        self.assertEqual(
            "Measurements require a saved canvas box for this capture.",
            result.message,
        )

    def test_optical_and_cdsem_setup_guides_expose_required_alignment_cards(self) -> None:
        from metrology_process_planner.ui.setup_guide import SetupGuidePresenter

        optical = SetupGuidePresenter().build(
            replace(session(), mode=SessionMode.OPTICAL_METROLOGY, setup=SetupState())
        )
        cdsem = SetupGuidePresenter().build(
            replace(session(), mode=SessionMode.CDSEM_CAPTURE, setup=SetupState())
        )

        optical_stages = {stage.stage_id: stage for stage in optical.stages}
        cdsem_stages = {stage.stage_id: stage for stage in cdsem.stages}
        self.assertIn("optical_alignment", optical_stages)
        self.assertTrue(optical_stages["optical_alignment"].required)
        self.assertEqual(
            "StartOpticalAlignmentCapture",
            optical_stages["optical_alignment"].primary_action,
        )
        self.assertIn("sem_alignment", cdsem_stages)
        self.assertTrue(cdsem_stages["sem_alignment"].required)

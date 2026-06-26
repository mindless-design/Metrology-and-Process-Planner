import unittest

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import MENU_COMMANDS, CommandId
from metrology_process_planner.ui.preview_widgets import PreviewPresenter
from metrology_process_planner.ui.review import PendingCaptureReviewPresenter
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.references import ArtifactRef
from tests.editor_render_fixtures import session

if __name__ == "__main__":
    unittest.main()


class UiLayerRedesignTestsPart1(unittest.TestCase):
    def test_menu_uses_primary_commands_and_router_results(self) -> None:
        services = build_app_services()
        titles = [spec.title for spec in MENU_COMMANDS]

        result = services.command_router.route(CommandId.OPEN_SETUP_GUIDE)
        unavailable = services.command_router.route(CommandId.OPEN_RECIPE_EDITOR)

        self.assertEqual(
            [
                "Start / Resume Measurement Setup",
                "Session Editor",
                "Open Session...",
                "New Session...",
                "Edit Recipe",
                "End Active Session",
                "Advanced Diagnostics",
                "Reporting Workbench",
            ],
            titles,
        )
        self.assertEqual("success", result.status)
        self.assertEqual("success", unavailable.status)

    def test_setup_guide_and_recipe_editor_are_view_model_surfaces(self) -> None:
        setup = SetupGuidePresenter().build(session())
        recipe = build_app_services().recipe_editor_controller.open_current()

        self.assertEqual("Demo", setup.session_name)
        self.assertIn("StartOriginPointCapture", setup.available_commands)
        self.assertEqual("unavailable", recipe.status)
        self.assertEqual("No recipe loaded", recipe.view_model.title)

    def test_preview_and_pending_review_are_generic_view_models(self) -> None:
        document = SessionDocumentBuilder().build(session())
        review = PendingCaptureReviewPresenter().build_selected(document)
        previews = PreviewPresenter().from_artifacts(
            (
                ArtifactRef(
                    "crop",
                    "images/missing.png",
                    artifact_id="artifact-001",
                    status="missing",
                    message="Missing crop",
                    repair_action="regenerate_artifact",
                    repair_suggestion="Regenerate the missing crop.",
                ),
            )
        )

        self.assertIsNotNone(review)
        self.assertEqual("pending-001", review.pending_id)
        self.assertEqual("Raw Site Image", previews[0].label)
        self.assertEqual("missing", previews[0].status)
        self.assertIn("Missing artifact: Missing crop", previews[0].placeholder)
        self.assertIn("Belongs to artifact-001 (crop)", previews[0].placeholder)
        self.assertIn("CSV export can continue", previews[0].placeholder)
        self.assertIn("reports may use this placeholder", previews[0].placeholder)
        self.assertIn("Repair: Regenerate the missing crop.", previews[0].placeholder)
        self.assertEqual("regenerate_artifact", previews[0].repair_action)
        self.assertEqual("Regenerate the missing crop.", previews[0].repair_suggestion)

    def test_report_output_previews_use_artifact_type_labels(self) -> None:
        previews = PreviewPresenter().from_artifacts(
            (
                ArtifactRef(
                    "report_output",
                    "reports/session-report.pptx",
                    artifact_id="report-001-pptx",
                    artifact_type="powerpoint_deck",
                ),
                ArtifactRef(
                    "report_output",
                    "reports/session-report.manifest.json",
                    artifact_id="report-001-manifest",
                    artifact_type="report_manifest",
                ),
            )
        )

        self.assertEqual("PowerPoint Deck", previews[0].label)
        self.assertEqual("Report Manifest", previews[1].label)

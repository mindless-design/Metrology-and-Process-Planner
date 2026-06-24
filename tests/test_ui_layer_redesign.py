import unittest

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import DEFAULT_COMMANDS, CommandId
from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import CanvasObjectType, SessionMode
from metrology_process_planner.ui.capture import (
    BoxCaptureTool,
    CaptureGesture,
    CaptureGesturePolicy,
    CaptureToolPresenter,
    LineCaptureTool,
    PointCaptureTool,
)
from metrology_process_planner.ui.preview_widgets import PreviewPresenter
from metrology_process_planner.ui.review import PendingCaptureReviewPresenter
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from metrology_process_planner.workflows import InteractionContext
from metrology_process_planner.workflows.compound_capture import (
    arm_inner_feature_capture,
    ellipsometry_request,
)
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.references import ArtifactRef
from tests.compound_capture_fixtures import pending_parent
from tests.editor_render_fixtures import session


class UiLayerRedesignTests(unittest.TestCase):
    def test_menu_uses_five_primary_commands_and_router_results(self) -> None:
        services = build_app_services()
        titles = [spec.title for spec in DEFAULT_COMMANDS]

        result = services.command_router.route(CommandId.START_OR_RESUME_SETUP)
        unavailable = services.command_router.route(CommandId.EDIT_RECIPE)

        self.assertEqual(
            [
                "Start / Resume Measurement Setup",
                "Session Editor",
                "Edit Recipe",
                "End Active Session",
                "Advanced Diagnostics",
            ],
            titles,
        )
        self.assertEqual("success", result.status)
        self.assertEqual("success", unavailable.status)

    def test_setup_guide_and_recipe_editor_are_view_model_surfaces(self) -> None:
        setup = SetupGuidePresenter().build(session())
        recipe = build_app_services().recipe_editor_controller.open_current()

        self.assertEqual("Demo", setup.session_name)
        self.assertIn("StartOriginCapture", setup.available_commands)
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
                ),
            )
        )

        self.assertIsNotNone(review)
        self.assertEqual("pending-001", review.pending_id)
        self.assertEqual("missing", previews[0].status)
        self.assertEqual("Missing crop", previews[0].placeholder)

    def test_capture_tools_share_shift_gesture_policy_and_status_view_model(self) -> None:
        policy = CaptureGesturePolicy()
        context = InteractionContext()
        box_tool = BoxCaptureTool(policy=policy)
        armed = box_tool.arm(context)

        ignored = box_tool.handle(session(), armed, CaptureGesture("drag_start", Point(0, 0)))
        started = box_tool.handle(
            session(),
            armed,
            CaptureGesture("drag_start", Point(0, 0), shift_pressed=True),
        )
        status = CaptureToolPresenter().build(LineCaptureTool().arm(context, "parent-001"))
        point_status = CaptureToolPresenter().build(PointCaptureTool().arm(context))

        self.assertFalse(ignored.handled)
        self.assertTrue(started.handled)
        self.assertEqual("Left Shift + drag line", status.gesture_hint)
        self.assertEqual("Left Shift + click point", point_status.gesture_hint)
        self.assertTrue(
            policy.accepts(
                CanvasObjectType.SITE_BOX,
                CaptureGesture("drag_update", Point(1, 1), True),
            )
        )

    def test_point_capture_returns_explicit_unavailable_result(self) -> None:
        tool = PointCaptureTool()
        current_session = session()
        context = tool.arm(InteractionContext(), "parent-001")

        ignored = tool.handle(
            current_session,
            context,
            CaptureGesture("click", Point(1, 1)),
        )
        unavailable = tool.handle(
            current_session,
            context,
            CaptureGesture("click", Point(1, 1), shift_pressed=True),
        )

        self.assertFalse(ignored.handled)
        self.assertTrue(unavailable.handled)
        self.assertEqual(("Point capture is not implemented yet.",), unavailable.messages)
        self.assertEqual(current_session, unavailable.session)

    def test_point_capture_adds_ellipsometry_child_during_compound_workflow(self) -> None:
        tool = PointCaptureTool()
        current_session = arm_inner_feature_capture(
            pending_parent(SessionMode.ELLIPSOMETRY_PLANNER),
            "pending-001",
            ellipsometry_request(),
        )
        context = tool.arm(InteractionContext(), "canvas-parent")

        result = tool.handle(
            current_session,
            context,
            CaptureGesture("click", Point(4, 4), shift_pressed=True),
        )

        self.assertTrue(result.handled)
        self.assertEqual(2, len(result.session.canvas_objects))
        self.assertEqual(
            CanvasObjectType.ELLIPSOMETRY_POINT,
            result.session.canvas_objects[1].object_type,
        )


if __name__ == "__main__":
    unittest.main()

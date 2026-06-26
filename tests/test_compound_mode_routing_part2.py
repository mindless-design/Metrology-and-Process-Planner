import unittest

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    ArtifactOutputDefinition,
    ArtifactPolicy,
    CaptureSequenceDefinition,
    ModeDefinition,
    ModeWorkflowPlanner,
    ProcessPolicy,
    SessionMode,
)
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_line_feature,
    arm_inner_feature_capture,
    save_composite_capture,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.compound_capture_fixtures import pending_parent


def _line_mode(mode_id: str = "project.fib_cut") -> ModeDefinition:
    return ModeDefinition(
        mode_id,
        "Project FIB Cut",
        family="process_aware",
        capture=CaptureSequenceDefinition(
            primitive_type="site_then_line",
            supported_primitives=("site_then_line",),
            site_role="fib_site",
            inner_feature_type="line_capture",
            inner_feature_role="fib_cut_line",
            inner_feature_kind="line",
            inner_feature_label="FIB Cut",
            child_canvas_object_type="fib_cut",
            validators=("inside_parent_box",),
            saved_capture_type="fib_site_line",
            extension_key="fib_process",
            feature_id_field="fib_cut_feature_id",
            process_output_key="outputs",
            repeat_label_template="FIB Site {sequence:02d}",
        ),
        artifacts=ArtifactPolicy(
            (
                ArtifactOutputDefinition("image", "site_image"),
                ArtifactOutputDefinition("layout_annotation", "fib_overlay"),
                ArtifactOutputDefinition("process_output", "fib_stack_json"),
            )
        ),
        process=ProcessPolicy("recommended", "full_stack_compressed", "fib_cross_section"),
    )

def _recipe_free_line_mode() -> ModeDefinition:
    return ModeDefinition(
        "project.review_line",
        "Project Review Line",
        family="generic_capture",
        capture=CaptureSequenceDefinition(
            primitive_type="site_then_line",
            supported_primitives=("site_then_line",),
            site_role="review_site",
            inner_feature_type="line_capture",
            inner_feature_role="review_line",
            inner_feature_kind="line",
            inner_feature_label="Review Line",
            child_canvas_object_type="measurement",
            validators=("inside_parent_box",),
            saved_capture_type="review_site_line",
            extension_key="review_line",
            feature_id_field="line_feature_id",
            repeat_label_template="Review Site {sequence:02d}",
        ),
        artifacts=ArtifactPolicy(
            (
                ArtifactOutputDefinition("image", "site_image"),
                ArtifactOutputDefinition("layout_annotation", "review_overlay"),
            )
        ),
        process=ProcessPolicy("forbidden", "none", ""),
    )

def _action_labels(document, item_id: str) -> set[str]:
    actions = DefaultSessionModeAdapter().actions(
        document.session,
        document.items_by_id[item_id],
    )
    return {action.label for action in actions}

if __name__ == "__main__":
    unittest.main()


class CompoundModeRoutingTestsPart2(unittest.TestCase):
    def test_recipe_free_compound_mode_does_not_create_process_placeholders(self) -> None:
        request = ModeWorkflowPlanner().compound_capture_request(_recipe_free_line_mode())
        session = arm_inner_feature_capture(
            pending_parent(SessionMode.SIMPLE_LABELED_CAPTURE),
            "pending-001",
            request,
        )
        session = add_line_feature(session, "pending-001", Point(1, 1), Point(3, 3), request)

        result = save_composite_capture(
            session,
            SaveCompositeCaptureCommand("pending-001"),
        )
        capture = result.session.captures[0]
        extension = capture.extensions["review_line"]

        self.assertEqual((), result.session.process_outputs)
        self.assertEqual((), result.session.warnings)
        self.assertNotIn("process_context_ref", extension)
        self.assertNotIn("solver_request", extension)
        self.assertNotIn("solver_result_id", extension)
        self.assertNotIn("outputs", extension)
        self.assertIn("capture-cap-001-review_overlay", result.session.artifacts)
        self.assertNotIn("capture-cap-001-process_output", result.session.artifacts)

    def test_custom_line_mode_label_flows_into_editor_actions(self) -> None:
        request = ModeWorkflowPlanner().compound_capture_request(_line_mode())
        session = arm_inner_feature_capture(
            pending_parent(SessionMode.PROCESS_AWARE_METROLOGY),
            "pending-001",
            request,
        )
        pending_document = SessionDocumentBuilder().build(session)

        pending_labels = _action_labels(pending_document, "pending:pending-001")

        self.assertIn("Retake FIB Cut", pending_labels)

        saved = add_line_feature(session, "pending-001", Point(1, 1), Point(3, 3), request)
        saved = save_composite_capture(
            saved,
            SaveCompositeCaptureCommand("pending-001"),
        ).session
        saved_document = SessionDocumentBuilder().build(saved)

        saved_labels = _action_labels(saved_document, "capture:cap-001")

        self.assertIn("Replace FIB Cut", saved_labels)
        self.assertIn("Regenerate Fib Overlay", saved_labels)

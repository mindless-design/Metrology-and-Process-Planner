import unittest
from dataclasses import replace

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    ArtifactOutputDefinition,
    ArtifactPolicy,
    CanvasObjectType,
    CaptureSequenceDefinition,
    ModeDefinition,
    ModeRegistry,
    ModeWorkflowPlanner,
    ProcessPolicy,
    SessionMode,
    WorkflowState,
)
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_line_feature,
    arm_inner_feature_capture,
    save_composite_capture,
)
from metrology_process_planner.workflows.compound_capture_routing import active_compound_request
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
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


class CompoundModeRoutingTestsPart1(unittest.TestCase):
    def test_active_line_request_comes_from_mode_policy(self) -> None:
        session = replace(
            pending_parent(SessionMode.PROCESS_AWARE_METROLOGY),
            workflow=WorkflowState(
                active=True,
                stage="site_then_line:child",
                active_mode="project.fib_cut",
                active_primitive="measurement",
                pending_item_ref="pending-001",
            ),
        )
        registry = ModeRegistry((_line_mode("project.fib_cut"),))

        request = active_compound_request(session, "line", registry)

        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual("project.fib_cut", request.mode_id)
        self.assertEqual("fib_site", request.site_role)
        self.assertEqual("fib_cut_line", request.child_role)
        self.assertEqual("full_stack_compressed", request.solver_operation)
        self.assertEqual("fib_overlay", request.annotation_role)
        self.assertEqual(("fib_stack_json",), request.process_artifact_roles)
        self.assertEqual("fib_cut", request.child_canvas_object_type)
        self.assertEqual("FIB Cut", request.child_label)

    def test_mismatched_child_kind_does_not_route_to_compound(self) -> None:
        session = replace(
            pending_parent(SessionMode.PROCESS_AWARE_METROLOGY),
            workflow=WorkflowState(
                active=True,
                stage="site_then_line:child",
                active_mode="project.fib_cut",
                active_primitive="point",
                pending_item_ref="pending-001",
            ),
        )

        request = active_compound_request(session, "point", ModeRegistry((_line_mode(),)))

        self.assertIsNone(request)

    def test_custom_line_mode_contract_flows_into_saved_capture(self) -> None:
        request = ModeWorkflowPlanner().compound_capture_request(_line_mode())
        session = arm_inner_feature_capture(
            pending_parent(SessionMode.PROCESS_AWARE_METROLOGY),
            "pending-001",
            request,
        )
        session = add_line_feature(session, "pending-001", Point(1, 1), Point(3, 3), request)

        result = save_composite_capture(
            session,
            SaveCompositeCaptureCommand("pending-001"),
        )
        capture = result.session.captures[0]

        self.assertEqual("fib_site_line", capture.type)
        self.assertEqual(CanvasObjectType.FIB_CUT, result.session.canvas_objects[1].object_type)
        self.assertEqual("FIB Cut", capture.geometry.features[0]["label"])
        self.assertIn("fib_process", capture.extensions)
        self.assertIn("capture-cap-001-fib_overlay", result.session.artifacts)
        self.assertIn("capture-cap-001-fib_stack_json", result.session.artifacts)
        self.assertEqual("feat-001", capture.extensions["fib_process"]["fib_cut_feature_id"])

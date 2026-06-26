import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ProcessOutputRecord,
    SessionMode,
    built_in_mode_registry,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import (
    session_without_pending,
)

if __name__ == "__main__":
    unittest.main()


class NonProcessModeHardeningTestsPart1(unittest.TestCase):
    def test_builtin_modes_forbid_recipe_solver_and_process_ui(self) -> None:
        registry = built_in_mode_registry()
        mode_ids = (
            SessionMode.SIMPLE_CAPTURE.value,
            SessionMode.SIMPLE_LABELED_CAPTURE.value,
            SessionMode.FAST_BATCH_CAPTURE.value,
            SessionMode.CAD_REVIEW.value,
            SessionMode.CAD_REVIEW_CAPTURE.value,
            SessionMode.OPTICAL_METROLOGY.value,
            SessionMode.CDSEM_CAPTURE.value,
            SessionMode.CDSEM_MEASUREMENT.value,
            SessionMode.CDSEM_PLANNING.value,
            SessionMode.GRID_MEASUREMENT.value,
        )

        for mode_id in mode_ids:
            with self.subTest(mode_id=mode_id):
                definition = registry.definition(mode_id)
                self.assertEqual("forbidden", definition.process.recipe_policy)
                self.assertEqual("none", definition.process.solver_operation)
                self.assertEqual("", definition.process.render_profile)
                self.assertFalse(definition.capabilities.supports_process_solver)
                self.assertFalse(definition.editor.process_context_visible)
                self.assertNotIn("process_outputs", definition.editor.navigator_groups)
                self.assertNotIn("attach_recipe", definition.editor.actions)
                self.assertEqual((), definition.artifacts.process_roles_on_capture_save())
                self.assertEqual((), definition.validation_warnings())

    def test_target_modes_declare_recipe_free_workflow_policies(self) -> None:
        registry = built_in_mode_registry()

        fast_batch = registry.definition(SessionMode.FAST_BATCH_CAPTURE.value)
        self.assertEqual("Capture {sequence:03d}", fast_batch.capture.repeat_label_template)
        self.assertFalse(fast_batch.capture.review)
        self.assertIn(
            "review_category",
            registry.definition(SessionMode.CAD_REVIEW.value).metadata.field_ids(),
        )
        self.assertIn(
            "review_category",
            registry.definition(SessionMode.CAD_REVIEW_CAPTURE.value).metadata.field_ids(),
        )
        optical = registry.definition(SessionMode.OPTICAL_METROLOGY.value)
        cdsem = registry.definition(SessionMode.CDSEM_CAPTURE.value)
        self.assertIn("required_optical_alignment_mark", optical.setup.stage_types)
        self.assertIn("required_sem_alignment_mark", cdsem.setup.stage_types)
        grid = registry.definition(SessionMode.GRID_MEASUREMENT.value)
        self.assertTrue(grid.capabilities.supports_grid_datasets)

    def test_simple_capture_editor_hides_process_groups_fields_and_actions(self) -> None:
        source = replace(
            session_without_pending(),
            process_outputs=(
                ProcessOutputRecord("out-001", "profile_image", "Profile Image"),
            ),
        )
        document = SessionDocumentBuilder().build(source)
        adapter = DefaultSessionModeAdapter()

        groups = {group.label for group in document.navigator_groups}
        dashboard = document.items_by_id["dashboard"]
        capture = document.items_by_id["capture:cap-001"]
        dashboard_fields = adapter.metadata_fields(source, dashboard)
        capture_actions = adapter.actions(source, capture)
        action_labels = {action.label: action for action in capture_actions}

        self.assertNotIn("Setup", groups)
        self.assertNotIn("Cross Sections", groups)
        self.assertFalse(any(field.key.startswith("process_") for field in dashboard_fields))
        self.assertTrue(action_labels["Replace Capture"].enabled)
        self.assertIn("Add Measurement", action_labels)
        self.assertIn("Regenerate Image", action_labels)
        self.assertIn("Export CSV", action_labels)
        self.assertNotIn(
            EditorActionType.ATTACH_RECIPE,
            {action.action_type for action in capture_actions},
        )
        self.assertNotIn(
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
            {action.action_type for action in capture_actions},
        )

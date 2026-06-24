import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import ProcessOutputRecord
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.process_context import (
    attach_recipe,
    detach_recipe,
    refresh_recipe_fingerprint,
    regenerate_process_outputs,
    validate_process_context,
)
from metrology_process_planner.workflows.process_context_models import (
    AttachRecipeCommand,
    DetachRecipeCommand,
    RefreshRecipeFingerprintCommand,
    RegenerateProcessOutputsCommand,
)
from tests.process_context_fixtures import (
    capture_session,
    custom_process_capture_session,
    dashboard_field,
    recipe_path,
)
from tests.process_context_fixtures import (
    session as base_session,
)


class ProcessContextWorkflowTests(unittest.TestCase):
    def test_attach_recipe_persists_identity_fingerprint_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = recipe_path(Path(folder))

            result = attach_recipe(base_session(), AttachRecipeCommand(str(path)))

        context = result.session.process_context
        self.assertEqual("recipe_gate_stack", context.recipe_id)
        self.assertEqual("Gate Stack", context.recipe_name)
        self.assertEqual("embed_minimal_summary", context.recipe_snapshot_policy)
        self.assertEqual(64, len(context.recipe_fingerprint))
        self.assertEqual(2, context.recipe_snapshot["step_count"])
        self.assertEqual("HybridCrossSectionSolver", context.solver_backend)

    def test_missing_recipe_path_becomes_structured_warning(self) -> None:
        result = attach_recipe(
            base_session(),
            AttachRecipeCommand("not-a-real-recipe.json"),
        )

        self.assertEqual("warning", result.status)
        self.assertEqual("PROCESS_RECIPE_FILE_NOT_FOUND", result.warnings[0].code)
        self.assertEqual(("process_context:active",), result.warnings[0].related_item_refs)

    def test_refresh_fingerprint_reports_mismatch_without_throwing(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = recipe_path(Path(folder))
            attached = attach_recipe(
                base_session(),
                AttachRecipeCommand(str(path)),
            ).session

            result = refresh_recipe_fingerprint(
                attached,
                RefreshRecipeFingerprintCommand("expected-different-fingerprint"),
            )

        self.assertEqual("success", result.status)
        self.assertEqual("PROCESS_RECIPE_FINGERPRINT_MISMATCH", result.warnings[0].code)

    def test_detach_and_validate_use_durable_warning_state(self) -> None:
        detached = detach_recipe(base_session(), DetachRecipeCommand("Cleared."))
        validated = validate_process_context(detached.session)

        self.assertEqual("Cleared.", detached.message)
        self.assertEqual("warning", validated.status)
        self.assertIn("warn-process_recipe_missing", validated.session.process_context.warning_ids)
        self.assertEqual("PROCESS_RECIPE_MISSING", validated.warnings[0].code)

    def test_regenerate_process_output_is_warning_only_until_solver_is_wired(self) -> None:
        result = regenerate_process_outputs(
            capture_session(),
            RegenerateProcessOutputsCommand("cap-001", solver_available=False),
        )

        self.assertEqual("warning", result.status)
        self.assertEqual("warn-cap-001-solver_backend_unavailable", result.warnings[0].id)
        self.assertEqual(("capture:cap-001",), result.warnings[0].related_item_refs)

    def test_editor_dispatcher_routes_attach_recipe_and_rebuilds_document(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = recipe_path(Path(folder))
            document = SessionDocumentBuilder().build(base_session())

            result = EditorActionDispatcher().dispatch(
                document,
                EditorAction(
                    EditorActionType.ATTACH_RECIPE,
                    "Attach",
                    "dashboard",
                    payload=(("recipe_path", str(path)),),
                ),
            )

        self.assertEqual("success", result.status)
        self.assertEqual("recipe_gate_stack", result.document.session.process_context.recipe_id)
        self.assertEqual("attached", dashboard_field(result.document, "process_recipe"))

    def test_dashboard_and_capture_expose_process_context_actions(self) -> None:
        document = SessionDocumentBuilder().build(capture_session())
        adapter = DefaultSessionModeAdapter()

        dashboard_actions = adapter.actions(document.session, document.items_by_id["dashboard"])
        capture_actions = adapter.actions(document.session, document.items_by_id["capture:cap-001"])

        self.assertIn(
            EditorActionType.ATTACH_RECIPE,
            {item.action_type for item in dashboard_actions},
        )
        self.assertIn(
            "Regenerate Process Outputs",
            {item.label for item in dashboard_actions},
        )
        self.assertIn(
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
            {item.action_type for item in capture_actions},
        )

    def test_dashboard_process_outputs_are_canonical_status_counts(self) -> None:
        session = replace(
            base_session(),
            process_outputs=(
                ProcessOutputRecord("out-001", "Profile", "profile", status="ready"),
                ProcessOutputRecord("out-002", "Stack", "stack", status="failed"),
                ProcessOutputRecord("out-003", "Cross Section", "cross", status="failed"),
            ),
        )
        document = SessionDocumentBuilder().build(session)

        self.assertEqual("failed:2, ready:1", dashboard_field(document, "process_outputs"))

    def test_custom_process_extension_drives_validation_and_metadata(self) -> None:
        document = SessionDocumentBuilder().build(custom_process_capture_session())
        fields = DefaultSessionModeAdapter().metadata_fields(
            document.session,
            document.items_by_id["capture:cap-001"],
        )
        values = {field.key: field.value for field in fields}

        self.assertEqual("full_stack_compressed", values["solver_operation"])
        self.assertEqual("target", values["process_window"])

        result = validate_process_context(document.session)

        self.assertEqual("warning", result.status)
        self.assertTrue(
            any(warning.code == "PROCESS_RECIPE_MISSING" for warning in result.warnings)
        )

if __name__ == "__main__":
    unittest.main()

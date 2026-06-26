import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session_without_pending


class NonProcessWarningVisibilityTests(unittest.TestCase):
    def test_process_warnings_are_hidden_from_recipe_free_dashboard_count(self) -> None:
        artifact_warning = WarningRecord(
            "artifact-missing",
            "Missing image",
            code="ARTIFACT_MISSING",
        )
        process_warning = WarningRecord(
            "process-missing",
            "Missing recipe",
            source="process_context",
            code="PROCESS_RECIPE_MISSING",
        )
        source = replace(
            session_without_pending(),
            warnings=(artifact_warning, process_warning),
        )
        document = SessionDocumentBuilder().build(source)
        dashboard = document.items_by_id["dashboard"]

        fields = DefaultSessionModeAdapter().metadata_fields(source, dashboard)
        warning_count = next(field.value for field in fields if field.key == "warning_count")

        self.assertEqual("1", warning_count)
        self.assertIn("warning:artifact-missing", document.items_by_id)
        self.assertNotIn("warning:process-missing", document.items_by_id)

    def test_solver_render_and_process_output_warnings_are_hidden_recipe_free(self) -> None:
        warnings = (
            WarningRecord(
                "solver-unavailable",
                "Solver backend unavailable",
                source="solver",
                code="SOLVER_BACKEND_UNAVAILABLE",
            ),
            WarningRecord(
                "render-profile-missing",
                "Render profile missing",
                source="render_profile",
                code="RENDER_PROFILE_MISSING",
            ),
            WarningRecord(
                "process-output-stale",
                "Process output stale",
                source="artifact",
                code="PROCESS_OUTPUT_STALE",
            ),
            WarningRecord(
                "artifact-missing",
                "Missing image",
                source="artifact",
                code="ARTIFACT_MISSING",
            ),
        )
        source = replace(session_without_pending(), warnings=warnings)

        document = SessionDocumentBuilder().build(source)
        dashboard = document.items_by_id["dashboard"]

        fields = DefaultSessionModeAdapter().metadata_fields(source, dashboard)
        warning_count = next(field.value for field in fields if field.key == "warning_count")

        self.assertEqual("1", warning_count)
        self.assertIn("warning:artifact-missing", document.items_by_id)
        self.assertNotIn("warning:solver-unavailable", document.items_by_id)
        self.assertNotIn("warning:render-profile-missing", document.items_by_id)
        self.assertNotIn("warning:process-output-stale", document.items_by_id)

    def test_hidden_process_artifact_warning_is_hidden_for_loaded_recipe_free_mode(
        self,
    ) -> None:
        source = replace(session_without_pending(), mode=SessionMode.PROFILOMETRY_PLANNER)
        artifact = ArtifactRecord(
            "legacy-stack-image",
            "process_output",
            "Legacy Stack Image",
            "process_outputs/cap-001-stack.png",
            ArtifactOwnerRef("capture", "cap-001", "stack_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                repair_action="regenerate_process_output",
                requires_recipe=True,
                requires_solver=True,
            ),
        )
        warning = WarningRecord(
            "legacy-stack-missing",
            "Legacy stack image is missing.",
            source="artifact",
            code="ARTIFACT_MISSING",
            related_artifact_refs=(artifact.id,),
        )
        registry = _recipe_free_registry_for(source.mode.value)
        source = replace(source, artifacts={artifact.id: artifact}, warnings=(warning,))

        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        dashboard = document.items_by_id["dashboard"]

        fields = DefaultSessionModeAdapter(registry).metadata_fields(source, dashboard)
        warning_count = next(field.value for field in fields if field.key == "warning_count")

        self.assertEqual("0", warning_count)
        self.assertNotIn("warning:legacy-stack-missing", document.items_by_id)


def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))


if __name__ == "__main__":
    unittest.main()

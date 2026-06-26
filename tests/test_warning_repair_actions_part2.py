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
    EditorActionType,
    RecordRef,
    SessionDocumentBuilder,
    SessionItem,
    SessionItemKind,
)
from tests.artifact_lifecycle_fixtures import artifact
from tests.artifact_lifecycle_fixtures import session as artifact_session
from tests.process_context_fixtures import capture_session


def _session_with_warning(code: str = "PROCESS_RECIPE_MISSING"):
    session = capture_session()
    warning = WarningRecord(
        id=f"warn-cap-001-{code.lower()}",
        message="Process output needs attention.",
        source="process_context",
        code=code,
        related_item_refs=("capture:cap-001",),
        repair_suggestion="Attach a recipe and regenerate process outputs.",
    )
    capture = replace(session.captures[0], warning_ids=(warning.id,))
    return replace(session, captures=(capture,), warnings=(warning,))

def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class WarningRepairActionTestsPart2(unittest.TestCase):
    def test_artifact_warning_exposes_repair_actions_with_payload(self) -> None:
        crop = replace(artifact("crop"), status=ArtifactStatus.MISSING)
        warning = WarningRecord(
            "artifact-crop-missing",
            "Missing crop",
            source="artifact",
            code="ARTIFACT_MISSING",
            related_artifact_refs=("crop",),
        )
        document = SessionDocumentBuilder().build(
            replace(artifact_session(artifacts={"crop": crop}), warnings=(warning,))
        )
        warning_item = document.items_by_id["warning:artifact-crop-missing"]

        actions = DefaultSessionModeAdapter().actions(document.session, warning_item)
        regenerate = next(
            action
            for action in actions
            if action.action_type is EditorActionType.REGENERATE_ARTIFACT
        )
        relink = next(
            action for action in actions if action.action_type is EditorActionType.RELINK_ARTIFACT
        )

        self.assertEqual("crop", dict(regenerate.payload)["artifact_id"])
        self.assertEqual("crop", dict(relink.payload)["artifact_id"])

    def test_hidden_process_artifact_warning_does_not_expose_repair_actions(self) -> None:
        source = replace(artifact_session(), mode=SessionMode.PROFILOMETRY_PLANNER)
        hidden = ArtifactRecord(
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
                regenerable=True,
            ),
        )
        warning = WarningRecord(
            "legacy-stack-missing",
            "Legacy stack image is missing.",
            source="artifact",
            code="ARTIFACT_MISSING",
            related_artifact_refs=(hidden.id,),
        )
        registry = _recipe_free_registry_for(source.mode.value)
        document = SessionDocumentBuilder(mode_registry=registry).build(
            replace(source, artifacts={hidden.id: hidden}, warnings=(warning,))
        )
        warning_item = document.items_by_id.get("warning:legacy-stack-missing")
        if warning_item is None:
            warning_item = SessionItem(
                "warning:legacy-stack-missing",
                SessionItemKind.WARNING,
                warning.message,
                "warning",
                record_ref=RecordRef("warning", warning.id),
                warning_ids=(warning.id,),
            )

        actions = DefaultSessionModeAdapter(registry).actions(document.session, warning_item)

        action_types = {action.action_type for action in actions}
        self.assertNotIn(EditorActionType.REGENERATE_ARTIFACT, action_types)
        self.assertNotIn(EditorActionType.RELINK_ARTIFACT, action_types)

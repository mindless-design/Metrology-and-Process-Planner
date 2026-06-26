import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    EditorPolicy,
    MetadataFieldDefinition,
    MetadataSchema,
    ModeCapabilities,
    ModeDefinition,
    ModeRegistry,
    SessionModeId,
    SetupDefinition,
    WarningRecord,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.editor.document import SessionItem, SessionItemKind
from metrology_process_planner.workflows.editor.references import RecordRef
from metrology_process_planner.workflows.editor.view_models import EditorActionType
from tests.editor_render_fixtures import session_without_pending


def _external_metrology_registry(
    *,
    uses_setup_guide: bool = False,
    supports_measurements: bool = False,
    include_capture_field: bool = False,
    navigator_groups: tuple[str, ...] | None = None,
    setup_stages: tuple[str, ...] = (),
) -> ModeRegistry:
    return ModeRegistry(
        (
            ModeDefinition(
                "external_mode",
                "External Mode",
                family="metrology",
                capabilities=ModeCapabilities(
                    uses_setup_guide=uses_setup_guide,
                    supports_grid_datasets=True,
                    supports_measurements=supports_measurements,
                ),
                setup=SetupDefinition(
                    required=bool(setup_stages),
                    can_skip=not bool(setup_stages),
                    stage_types=setup_stages,
                ),
                metadata=_metadata(include_capture_field),
                editor=EditorPolicy(
                    navigator_groups or ("dashboard", "setup", "captures", "warnings")
                ),
            ),
        )
    )

def _metadata(include_capture_field: bool) -> MetadataSchema:
    if not include_capture_field:
        return MetadataSchema()
    return MetadataSchema(
        capture_fields=(MetadataFieldDefinition("external_field", "External Field"),)
    )

if __name__ == "__main__":
    unittest.main()


class ExternalModeEditorPolicyTestsPart3(unittest.TestCase):
    def test_registered_external_recipe_free_mode_hides_process_warnings(self) -> None:
        registry = _external_metrology_registry(navigator_groups=("dashboard", "warnings"))
        warning = WarningRecord(
            "warn-process-context",
            "Recipe is missing.",
            source="process_context",
            code="PROCESS_RECIPE_MISSING",
        )
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            warnings=(warning,),
        )

        document = SessionDocumentBuilder(mode_registry=registry).build(source)

        self.assertNotIn("warning:warn-process-context", document.items_by_id)
        self.assertEqual((), document.warning_view_models)
        self.assertEqual(["Dashboard"], [group.label for group in document.navigator_groups])

    def test_external_recipe_free_mode_warning_actions_hide_process_repairs(self) -> None:
        registry = _external_metrology_registry(navigator_groups=("dashboard", "warnings"))
        warning = WarningRecord(
            "warn-process-context",
            "Recipe is missing.",
            source="process_context",
            code="PROCESS_RECIPE_MISSING",
            related_item_refs=("capture:cap-001",),
        )
        source = replace(
            session_without_pending(),
            mode=SessionModeId("external_mode"),
            warnings=(warning,),
        )
        warning_item = SessionItem(
            "warning:warn-process-context",
            SessionItemKind.WARNING,
            "Recipe is missing.",
            "warning",
            record_ref=RecordRef("warning", "warn-process-context"),
            warning_ids=("warn-process-context",),
        )

        actions = DefaultSessionModeAdapter(registry).actions(source, warning_item)

        self.assertIn(EditorActionType.IGNORE_WARNING, {action.action_type for action in actions})
        self.assertNotIn(EditorActionType.ATTACH_RECIPE, {action.action_type for action in actions})
        self.assertNotIn(
            EditorActionType.VALIDATE_PROCESS_CONTEXT,
            {action.action_type for action in actions},
        )
        self.assertNotIn(
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
            {action.action_type for action in actions},
        )

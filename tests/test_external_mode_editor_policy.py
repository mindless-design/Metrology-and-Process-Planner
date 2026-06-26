import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    EditorPolicy,
    MetadataFieldDefinition,
    MetadataSchema,
    ModeCapabilities,
    ModeDefinition,
    ModeRegistry,
    SessionModeId,
    SetupDefinition,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
    SessionEditorCallbacks,
    SessionEditorShell,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
    select_item,
)
from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType
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


class ExternalModeEditorPolicyTestsPart1(unittest.TestCase):
    def test_registered_external_mode_policy_shapes_editor_view_models(self) -> None:
        registry = _external_metrology_registry(
            uses_setup_guide=True,
            supports_measurements=True,
            include_capture_field=True,
        )
        source = replace(session_without_pending(), mode=SessionModeId("external_mode"))
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        capture_document = select_item(document, "capture:cap-001")
        adapter = DefaultSessionModeAdapter(registry)

        dashboard_actions = adapter.actions(document.session, document.items_by_id["dashboard"])
        capture_actions = adapter.actions(
            capture_document.session,
            capture_document.items_by_id["capture:cap-001"],
        )
        capture_fields = adapter.metadata_fields(
            capture_document.session,
            capture_document.items_by_id["capture:cap-001"],
        )

        self.assertIn("setup", document.items_by_id)
        self.assertIn("Generate Metrology Overview", [action.label for action in dashboard_actions])
        self.assertIn("Generate Grid Overview", [action.label for action in dashboard_actions])
        self.assertIn("Add Measurement", [action.label for action in capture_actions])
        self.assertIn("external_field", [field.key for field in capture_fields])

    def test_registered_external_mode_policy_reaches_overview_dispatch(self) -> None:
        registry = _external_metrology_registry()
        source = replace(session_without_pending(), mode=SessionModeId("external_mode"))
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            dispatcher = EditorActionDispatcher(paths=paths, mode_registry=registry)

            metrology = dispatcher.dispatch(
                document,
                EditorAction(
                    EditorActionType.GENERATE_METROLOGY_OVERVIEW,
                    "Generate Metrology Overview",
                    "dashboard",
                ),
            )
            grid = dispatcher.dispatch(
                metrology.document,
                EditorAction(
                    EditorActionType.GENERATE_GRID_OVERVIEW,
                    "Generate Grid Overview",
                    "dashboard",
                ),
            )

        self.assertEqual("success", metrology.status)
        self.assertEqual("success", grid.status)

    def test_registered_external_recipe_free_mode_shapes_editor_header(self) -> None:
        registry = _external_metrology_registry(uses_setup_guide=True)
        source = replace(session_without_pending(), mode=SessionModeId("external_mode"))
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        adapter = DefaultSessionModeAdapter(registry)

        window = SessionEditorShell(InMemorySessionEditorWidgetFactory()).open(
            document,
            adapter,
            SessionEditorCallbacks(lambda _item_id: None, lambda _action: None),
        )

        header = dict(window["header"])
        action_labels = {action.label for action in window["primary_actions"]}
        self.assertIn("Setup", header)
        self.assertIn("Reopen Setup", action_labels)
        self.assertIn("Add Capture", action_labels)
        self.assertNotIn("Process Context", header)
        self.assertNotIn("Attach Recipe", action_labels)
        self.assertNotIn("Validate Process Context", action_labels)

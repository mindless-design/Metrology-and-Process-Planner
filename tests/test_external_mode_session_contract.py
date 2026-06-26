import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    MetadataFieldDefinition,
    MetadataSchema,
    ModeCapabilities,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SessionModeId,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    NewSessionRequest,
    SessionDocumentBuilder,
    SessionDocumentStore,
    SessionStore,
    select_item,
)
from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType
from tests.editor_render_fixtures import session_without_pending


class ExternalModeSessionContractTests(unittest.TestCase):
    def test_registered_external_mode_round_trips_through_session_document(self) -> None:
        registry = ModeRegistry((ModeDefinition("external_mode", "External Mode"),))
        with tempfile.TemporaryDirectory() as temp_dir:
            output_folder = Path(temp_dir)
            store = SessionStore(mode_registry=registry)
            created = store.new_session(
                NewSessionRequest(
                    output_folder,
                    "External Session",
                    SessionModeId("external_mode"),
                )
            )
            reopened = SessionDocumentStore(mode_registry=registry).load(output_folder)
            saved = json.loads((output_folder / "session.json").read_text(encoding="utf-8"))

        self.assertEqual("external_mode", created.session.mode.value)
        self.assertEqual("external_mode", reopened.session.mode.value)
        self.assertEqual("external_mode", saved["session"]["mode"])
        self.assertFalse(
            any(warning.code == "unsupported_mode" for warning in reopened.session.warnings)
        )

    def test_registered_external_mode_policy_shapes_editor_view_models(self) -> None:
        registry = _external_metrology_registry()
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
        registry = ModeRegistry(
            (
                ModeDefinition(
                    "external_mode",
                    "External Mode",
                    family="metrology",
                    capabilities=ModeCapabilities(supports_grid_datasets=True),
                ),
            )
        )
        source = replace(session_without_pending(), mode=SessionModeId("external_mode"))
        document = SessionDocumentBuilder(mode_registry=registry).build(source)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            dispatcher = EditorActionDispatcher(paths=paths, mode_registry=registry)

            metrology = _dispatch_overview(
                dispatcher,
                document,
                EditorActionType.GENERATE_METROLOGY_OVERVIEW,
                "Generate Metrology Overview",
            )
            grid = _dispatch_overview(
                dispatcher,
                metrology.document,
                EditorActionType.GENERATE_GRID_OVERVIEW,
                "Generate Grid Overview",
            )

        self.assertEqual("success", metrology.status)
        self.assertEqual("success", grid.status)

    def test_unregistered_external_mode_still_falls_back_with_warning(self) -> None:
        session = SessionRecord.from_dict(
            {
                "id": "session-1",
                "label": "Fallback Session",
                "mode": "missing_external_mode",
                "created_at": "2026-01-01T00:00:00",
            }
        )

        self.assertEqual(SessionMode.SIMPLE_CAPTURE, session.mode)
        self.assertTrue(any(warning.code == "unsupported_mode" for warning in session.warnings))


def _external_metrology_registry() -> ModeRegistry:
    return ModeRegistry(
        (
            ModeDefinition(
                "external_mode",
                "External Mode",
                family="metrology",
                capabilities=ModeCapabilities(
                    uses_setup_guide=True,
                    supports_grid_datasets=True,
                    supports_measurements=True,
                ),
                metadata=MetadataSchema(
                    capture_fields=(MetadataFieldDefinition("external_field", "External Field"),)
                ),
            ),
        )
    )


def _dispatch_overview(dispatcher, document, action_type, label):
    return dispatcher.dispatch(document, EditorAction(action_type, label, "dashboard"))


if __name__ == "__main__":
    unittest.main()

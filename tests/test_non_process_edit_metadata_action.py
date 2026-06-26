import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session
from tests.measurement_child_fixtures import saved_measurement_document


class NonProcessEditMetadataActionTests(unittest.TestCase):
    def test_saved_non_process_captures_expose_edit_metadata_action(self) -> None:
        for mode in (
            SessionMode.SIMPLE_CAPTURE,
            SessionMode.FAST_BATCH_CAPTURE,
            SessionMode.CAD_REVIEW,
            SessionMode.OPTICAL_METROLOGY,
            SessionMode.CDSEM_MEASUREMENT,
        ):
            with self.subTest(mode=mode.value):
                document = SessionDocumentBuilder().build(replace(session(), mode=mode))
                item = document.items_by_id["capture:cap-001"]

                actions = DefaultSessionModeAdapter().actions(document.session, item)

                edit = _action_by_label(actions, "Edit Metadata")
                self.assertEqual(EditorActionType.EDIT_METADATA, edit.action_type)
                self.assertEqual("capture:cap-001", edit.item_id)

    def test_saved_measurements_expose_edit_metadata_action(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            document = saved_measurement_document(paths)
        item = document.items_by_id["measurement:meas-001"]

        actions = DefaultSessionModeAdapter().actions(document.session, item)

        edit = _action_by_label(actions, "Edit Metadata")
        self.assertEqual(EditorActionType.EDIT_METADATA, edit.action_type)
        self.assertEqual("measurement:meas-001", edit.item_id)

    def test_edit_metadata_routes_without_dialog_or_mode_specific_handler(self) -> None:
        document = SessionDocumentBuilder().build(replace(session(), mode=SessionMode.CAD_REVIEW))
        action = _action_by_label(
            DefaultSessionModeAdapter().actions(
                document.session,
                document.items_by_id["capture:cap-001"],
            ),
            "Edit Metadata",
        )

        result = EditorActionDispatcher().dispatch(document, action)

        self.assertEqual("success", result.status)
        self.assertEqual("Metadata editor ready.", result.message)
        self.assertEqual("capture:cap-001", result.document.selection.selected_item_id)


def _action_by_label(actions, label):
    return next(action for action in actions if action.label == label)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.rendering.overview import user_labels_from_session
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType
from tests.editor_render_fixtures import session_without_pending


class OverviewDispatcherPolicyTests(unittest.TestCase):
    def test_direct_metrology_overview_is_unavailable_outside_metrology_mode(self) -> None:
        result = _dispatch(
            session_without_pending(),
            EditorActionType.GENERATE_METROLOGY_OVERVIEW,
        )

        self.assertEqual("unavailable", result.status)
        self.assertIn("Metrology overview", result.message)

    def test_direct_grid_overview_is_unavailable_outside_grid_mode(self) -> None:
        result = _dispatch(session_without_pending(), EditorActionType.GENERATE_GRID_OVERVIEW)

        self.assertEqual("unavailable", result.status)
        self.assertIn("Grid overview", result.message)

    def test_mode_appropriate_overview_actions_still_generate(self) -> None:
        optical = replace(session_without_pending(), mode=SessionMode.OPTICAL_METROLOGY)
        grid = replace(session_without_pending(), mode=SessionMode.GRID_MEASUREMENT)

        metrology = _dispatch(optical, EditorActionType.GENERATE_METROLOGY_OVERVIEW)
        self.assertEqual("success", _dispatch(grid, EditorActionType.GENERATE_GRID_OVERVIEW).status)
        self.assertEqual("success", metrology.status)

    def test_add_user_label_persists_overview_extension(self) -> None:
        result = _dispatch(
            session_without_pending(),
            EditorActionType.ADD_USER_LABEL,
            payload=(("title", "Inspect corner"), ("left", "5"), ("right", "12")),
        )

        labels = user_labels_from_session(result.document.session)
        self.assertEqual("success", result.status)
        self.assertEqual(1, len(labels))
        self.assertEqual("Inspect corner", labels[0].title)
        self.assertEqual("box", labels[0].geometry["kind"])


def _dispatch(source, action_type: EditorActionType, payload=()):
    document = SessionDocumentBuilder().build(source)
    with tempfile.TemporaryDirectory() as temp_dir:
        paths = SessionPaths.for_folder(Path(temp_dir))
        paths.ensure_created()
        return EditorActionDispatcher(paths=paths).dispatch(
            document,
            EditorAction(action_type, "Generate", "dashboard", payload=payload),
        )


if __name__ == "__main__":
    unittest.main()

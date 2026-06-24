import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_line_feature,
    arm_inner_feature_capture,
    profilometry_request,
    save_composite_capture,
)
from metrology_process_planner.workflows.editor import (
    EditorAction,
    EditorActionDispatcher,
    EditorActionType,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.process_context import attach_recipe
from metrology_process_planner.workflows.process_context_models import AttachRecipeCommand
from tests.compound_capture_fixtures import pending_parent
from tests.process_context_fixtures import recipe_path


class DashboardProcessOutputActionTests(unittest.TestCase):
    def test_dashboard_regenerates_all_process_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            document = SessionDocumentBuilder().build(_profile_session_with_recipe(Path(folder)))

            result = EditorActionDispatcher().dispatch(
                document,
                EditorAction(
                    EditorActionType.REGENERATE_PROCESS_OUTPUT,
                    "Regenerate Process Outputs",
                    "dashboard",
                ),
            )

        self.assertEqual("success", result.status)
        self.assertEqual("ready", result.document.session.process_outputs[0].status)


def _profile_session_with_recipe(folder: Path):
    saved = _profile_session_without_recipe()
    path = recipe_path(folder)
    return attach_recipe(saved, AttachRecipeCommand(str(path))).session


def _profile_session_without_recipe():
    session = arm_inner_feature_capture(
        pending_parent(SessionMode.PROFILOMETRY_PLANNER),
        "pending-001",
        profilometry_request(),
    )
    session = add_line_feature(
        session,
        "pending-001",
        Point(1, 1),
        Point(9, 9),
        profilometry_request(),
    )
    return save_composite_capture(
        session,
        SaveCompositeCaptureCommand("pending-001", "Profile Site 01"),
    ).session


if __name__ == "__main__":
    unittest.main()

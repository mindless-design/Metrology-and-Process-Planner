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
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.process_context import attach_recipe
from metrology_process_planner.workflows.process_context_models import AttachRecipeCommand
from tests.compound_capture_fixtures import pending_parent
from tests.process_context_fixtures import recipe_path


class ProcessCaptureMetadataFieldTests(unittest.TestCase):
    def test_process_aware_capture_exposes_context_and_output_status(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            session = _profile_session_with_recipe(Path(folder))
            document = SessionDocumentBuilder().build(session)

        fields = _field_values(document, "capture:cap-001")

        self.assertEqual("Gate Stack", fields["process_recipe"])
        self.assertEqual("line_profile", fields["solver_operation"])
        self.assertEqual("target", fields["process_window"])
        self.assertEqual("pending_solver:1", fields["process_outputs"])
        self.assertEqual("1", fields["process_warnings"])


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


def _field_values(document, item_id: str) -> dict[str, str]:
    fields = DefaultSessionModeAdapter().metadata_fields(
        document.session,
        document.items_by_id[item_id],
    )
    return {field.key: field.value for field in fields}


if __name__ == "__main__":
    unittest.main()

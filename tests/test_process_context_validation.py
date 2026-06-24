import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import ArtifactStatus, SessionMode
from metrology_process_planner.workflows.compound_capture import (
    SaveCompositeCaptureCommand,
    add_line_feature,
    arm_inner_feature_capture,
    profilometry_request,
    save_composite_capture,
)
from metrology_process_planner.workflows.process_context import (
    attach_recipe,
    validate_process_context,
)
from metrology_process_planner.workflows.process_context_models import (
    AttachRecipeCommand,
    ValidateProcessContextCommand,
)
from tests.compound_capture_fixtures import pending_parent
from tests.process_context_fixtures import recipe_path


class ProcessContextValidationTests(unittest.TestCase):
    def test_process_aware_capture_without_render_profile_warns(self) -> None:
        result = validate_process_context(
            _profile_session_without_recipe(),
            ValidateProcessContextCommand(require_recipe=False),
        )

        self.assertIn("RENDER_PROFILE_MISSING", _codes(result.warnings))

    def test_stale_process_output_warns_for_capture_repair(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            session = _profile_session_with_recipe(Path(folder))
            output = replace(session.process_outputs[0], status="stale")
            session = replace(session, process_outputs=(output,))

            result = validate_process_context(session)

        self.assertIn("PROCESS_OUTPUT_STALE", _codes(result.warnings))
        self.assertEqual(("capture:cap-001",), result.warnings[0].related_item_refs)

    def test_stale_process_artifact_warns_for_capture_repair(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            session = _profile_session_with_recipe(Path(folder))
            artifact = session.artifacts["capture-cap-001-profile_image"]
            artifacts = dict(session.artifacts)
            artifacts[artifact.id] = replace(artifact, status=ArtifactStatus.STALE)

            result = validate_process_context(replace(session, artifacts=artifacts))

        self.assertIn("PROCESS_OUTPUT_STALE", _codes(result.warnings))

    def test_capture_missing_active_process_context_ref_warns(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            session = _profile_session_with_recipe(Path(folder))
            capture = session.captures[0]
            extension = dict(capture.extensions["profilometry"])
            extension.pop("process_context_ref")
            capture = replace(capture, extensions={"profilometry": extension})

            result = validate_process_context(replace(session, captures=(capture,)))

        self.assertIn("PROCESS_RECIPE_MISSING", _codes(result.warnings))
        self.assertEqual(("capture:cap-001",), result.warnings[0].related_item_refs)


def _profile_session_with_recipe(folder: Path):
    path = recipe_path(folder)
    return attach_recipe(_profile_session_without_recipe(), AttachRecipeCommand(str(path))).session


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


def _codes(warnings) -> set[str]:
    return {warning.code for warning in warnings}


if __name__ == "__main__":
    unittest.main()

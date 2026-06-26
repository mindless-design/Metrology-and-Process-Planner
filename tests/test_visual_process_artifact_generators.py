import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import ArtifactStatus
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from tests.process_output_fixtures import profile_session_with_recipe


class VisualProcessArtifactGeneratorTests(unittest.TestCase):
    def test_profile_artifact_repair_writes_rendered_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir) / "session")
            paths.ensure_created()
            source = _missing_visual_artifact(
                profile_session_with_recipe(Path(temp_dir)),
                "capture-cap-001-profile_image",
            )

            repaired = ArtifactRepairService().repair_artifact(
                source,
                "capture-cap-001-profile_image",
                paths,
            )
            artifact = repaired.artifacts["capture-cap-001-profile_image"]
            output = artifact_path_to_disk(paths.folder, artifact.relative_path)
            output_exists = output.exists()
            output_text = output.read_text(encoding="utf-8") if output_exists else ""

        self.assertEqual(ArtifactStatus.PRESENT, artifact.status)
        self.assertEqual("profile_image", artifact.type)
        self.assertTrue(output_exists)
        self.assertIn("<svg", output_text)
        self.assertEqual("ready", repaired.process_outputs[0].status)
        self.assertEqual(
            "profilometry_surface",
            artifact.extensions["cross_section_render"]["render_mode_id"],
        )

    def test_cross_section_artifact_repair_uses_role_specific_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir) / "session")
            paths.ensure_created()
            source = _missing_visual_artifact(
                profile_session_with_recipe(Path(temp_dir)),
                "capture-cap-001-cross_section_image",
            )

            repaired = ArtifactRepairService().repair_artifact(
                source,
                "capture-cap-001-cross_section_image",
                paths,
            )
            artifact = repaired.artifacts["capture-cap-001-cross_section_image"]
            output = artifact_path_to_disk(paths.folder, artifact.relative_path)
            output_exists = output.exists()

        self.assertEqual(ArtifactStatus.PRESENT, artifact.status)
        self.assertEqual("cross_section_image", artifact.type)
        self.assertTrue(output_exists)
        self.assertEqual(
            "proportional_physical",
            artifact.extensions["cross_section_render"]["render_mode_id"],
        )


def _missing_visual_artifact(session, artifact_id):
    artifact = session.artifacts[artifact_id]
    return replace(
        session,
        artifacts={
            **dict(session.artifacts),
            artifact_id: replace(artifact, status=ArtifactStatus.MISSING),
        },
    )


if __name__ == "__main__":
    unittest.main()

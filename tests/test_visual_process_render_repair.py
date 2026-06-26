import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from tests.process_output_fixtures import (
    profile_session_with_recipe,
    profile_session_without_recipe,
)


class VisualProcessRenderRepairTests(unittest.TestCase):
    def test_profile_render_generator_repairs_visual_process_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir) / "session")
            paths.ensure_created()
            source = _session_with_visual_profile_artifact(
                profile_session_with_recipe(Path(temp_dir)),
            )
            artifact_id = "capture-cap-001-profile_render_svg"

            repaired = ArtifactRepairService().repair_artifact(source, artifact_id, paths)
            artifact = repaired.artifacts[artifact_id]
            output = artifact_path_to_disk(paths.folder, artifact.relative_path)
            output_exists = output.exists()
            output_text = output.read_text(encoding="utf-8")

        self.assertEqual(ArtifactStatus.PRESENT, artifact.status)
        self.assertEqual("CrossSectionRenderingPipeline/1", artifact.generator)
        self.assertEqual("image/svg+xml", artifact.file.content_type)
        self.assertIn("cross_section_render", artifact.extensions)
        self.assertEqual(
            artifact.id,
            repaired.process_outputs[0].artifact_refs["profile_image"],
        )
        self.assertTrue(output_exists)
        self.assertIn("<svg", output_text)

    def test_profile_render_generator_requires_recipe(self) -> None:
        source = _session_with_visual_profile_artifact(profile_session_without_recipe())
        artifact_id = "capture-cap-001-profile_render_svg"

        requests = ArtifactRepairService().build_repair_requests(source)
        request = next(item for item in requests if item.artifact_id == artifact_id)

        self.assertEqual("unavailable", request.status.value)
        self.assertIn("RECIPE_REQUIRED_FOR_REPAIR", request.requirements)


def _session_with_visual_profile_artifact(source):
    artifact = ArtifactRecord(
        "capture-cap-001-profile_render_svg",
        "profile_image",
        "Profile render",
        "artifacts/render/cap-001-profile.svg",
        ArtifactOwnerRef("capture", "cap-001", "profile_image"),
        status=ArtifactStatus.MISSING,
        generator="profile_render",
        repair=ArtifactRepairMetadata(
            "regenerate_process_render",
            "Regenerate visual process render.",
            regenerable=True,
            requires_recipe=True,
            requires_solver=True,
        ),
    )
    return replace(source, artifacts={**dict(source.artifacts), artifact.id: artifact})


if __name__ == "__main__":
    unittest.main()

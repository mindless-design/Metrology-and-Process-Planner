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
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.rendering.overview import generate_overview_artifact
from metrology_process_planner.workflows.artifacts import (
    ArtifactRepairService,
    ArtifactScanner,
)
from metrology_process_planner.workflows.editor.csv_export_artifacts import (
    with_csv_export_artifact,
)
from tests.artifact_lifecycle_fixtures import session as artifact_session
from tests.measurement_child_fixtures import saved_measurement_document
from tests.process_output_fixtures import (
    profile_session_with_recipe,
    profile_session_without_recipe,
)


class ArtifactGeneratorHandlerTests(unittest.TestCase):
    def test_builtin_csv_generator_repairs_stale_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            source = _session_with_csv(paths)
            edited = replace(source, name="Edited Export")
            stale, _result = ArtifactScanner().scan_session(edited, paths)
            artifact_id = next(iter(stale.artifacts))

            repaired = ArtifactRepairService().repair_artifact(stale, artifact_id, paths)
            csv_text = paths.capture_csv.read_text(encoding="utf-8")

        self.assertEqual(ArtifactStatus.PRESENT, repaired.artifacts[artifact_id].status)
        self.assertIn("Edited Export", csv_text)

    def test_builtin_placeholder_generator_writes_visible_svg(self) -> None:
        target = ArtifactRecord(
            "placeholder-001",
            "placeholder",
            "Missing image",
            "artifacts/placeholders/missing.svg",
            ArtifactOwnerRef("capture", "cap-001", "placeholder"),
            status=ArtifactStatus.MISSING,
            generator="placeholder_image",
            repair=ArtifactRepairMetadata(
                regenerable=True,
                placeholder_reason="Source image is unavailable.",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            source = artifact_session(artifacts={target.id: target})

            repaired = ArtifactRepairService().repair_artifact(source, target.id, paths)
            output = artifact_path_to_disk(paths.folder, target.relative_path)
            output_exists = output.exists()

        self.assertEqual(ArtifactStatus.PRESENT, repaired.artifacts[target.id].status)
        self.assertTrue(output_exists)

    def test_measurement_annotation_generator_updates_session_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)
            measurement = document.session.captures[0].measurements[0]
            artifact_id = measurement.artifact_refs["measurement_annotation_svg"]
            missing = replace(
                document.session.artifacts[artifact_id],
                status=ArtifactStatus.MISSING,
                generator="measurement_annotation",
                repair=ArtifactRepairMetadata(regenerable=True),
            )
            source = replace(
                document.session,
                artifacts={**dict(document.session.artifacts), artifact_id: missing},
            )
            artifact_path_to_disk(paths.folder, missing.relative_path).unlink()

            repaired = ArtifactRepairService().repair_artifact(source, artifact_id, paths)
            output = artifact_path_to_disk(
                paths.folder,
                repaired.artifacts[artifact_id].relative_path,
            )
            output_exists = output.exists()

        self.assertEqual(ArtifactStatus.PRESENT, repaired.artifacts[artifact_id].status)
        self.assertTrue(output_exists)
        self.assertIn("measurement_detail", repaired.captures[0].measurements[0].artifact_refs)

    def test_overview_generator_repairs_missing_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            source = generate_overview_artifact(artifact_session(), paths.folder)
            artifact_id = next(iter(source.artifacts))
            artifact = source.artifacts[artifact_id]
            artifact_path_to_disk(paths.folder, artifact.relative_path).unlink()
            scanned, _result = ArtifactScanner().scan_session(source, paths)

            repaired = ArtifactRepairService().repair_artifact(scanned, artifact_id, paths)
            output = artifact_path_to_disk(
                paths.folder,
                repaired.artifacts[artifact_id].relative_path,
            )
            output_exists = output.exists()

        self.assertEqual(ArtifactStatus.PRESENT, repaired.artifacts[artifact_id].status)
        self.assertTrue(output_exists)
        self.assertEqual("overview_diagram_renderer", repaired.artifacts[artifact_id].generator)

    def test_process_output_generator_repairs_pending_solver_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir) / "session")
            paths.ensure_created()
            source = profile_session_with_recipe(Path(temp_dir))
            artifact_id = "capture-cap-001-profile_image"

            repaired = ArtifactRepairService().repair_artifact(source, artifact_id, paths)
            output = artifact_path_to_disk(
                paths.folder,
                repaired.artifacts[artifact_id].relative_path,
            )
            output_exists = output.exists()

        self.assertEqual(ArtifactStatus.PRESENT, repaired.artifacts[artifact_id].status)
        self.assertTrue(output_exists)
        self.assertEqual("ready", repaired.process_outputs[0].status)

    def test_process_output_generator_is_unavailable_without_recipe(self) -> None:
        source = profile_session_without_recipe()
        artifact_id = "capture-cap-001-profile_image"
        source = replace(
            source,
            artifacts={
                **dict(source.artifacts),
                artifact_id: replace(
                    source.artifacts[artifact_id],
                    status=ArtifactStatus.MISSING,
                ),
            },
        )

        requests = ArtifactRepairService().build_repair_requests(source)
        request = next(item for item in requests if item.artifact_id == artifact_id)

        self.assertEqual(artifact_id, request.artifact_id)
        self.assertEqual("unavailable", request.status.value)
        self.assertIn("RECIPE_REQUIRED_FOR_REPAIR", request.requirements)


def _session_with_csv(paths: SessionPaths):
    source = artifact_session()
    destination = CaptureCsvExporter().export(source, paths.capture_csv)
    return with_csv_export_artifact(source, paths, destination)


if __name__ == "__main__":
    unittest.main()

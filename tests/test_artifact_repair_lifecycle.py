import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactOwnerRef,
    ArtifactRepairMetadata,
    ArtifactStatus,
    SourceLayoutContext,
)
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import (
    ArtifactGeneratorRegistry,
    ArtifactRepairService,
    GeneratorRegistration,
)
from tests.artifact_lifecycle_fixtures import artifact, session, temp_paths


class ArtifactRepairLifecycleTests(unittest.TestCase):
    def test_unavailable_repair_preserves_status_and_adds_warning(self) -> None:
        measurement = replace(
            artifact("measurement"),
            type="measurement_detail_image",
            owner=ArtifactOwnerRef("measurement", "meas-001", "annotation"),
            dependencies=(ArtifactDependencyRef(artifact_id="parent"),),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(regenerable=True, requires_parent_image=True),
        )
        source = session(artifacts={"measurement": measurement})

        repaired = ArtifactRepairService().repair_artifact(source, "measurement", temp_paths())

        self.assertEqual(ArtifactStatus.MISSING, repaired.artifacts["measurement"].status)
        self.assertNotIn("placeholder", repaired.artifacts["measurement"].extensions)
        self.assertIn(
            "PARENT_IMAGE_REQUIRED_FOR_REPAIR",
            {warning.code for warning in repaired.warnings},
        )

    def test_repair_request_without_handler_is_unavailable(self) -> None:
        crop = replace(
            artifact("crop"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(regenerable=True),
        )
        source = replace(
            session(artifacts={"crop": crop}),
            source_layout=SourceLayoutContext(layout_path="source.gds"),
        )

        requests = ArtifactRepairService().build_repair_requests(source)

        self.assertEqual(("crop",), tuple(request.artifact_id for request in requests))
        self.assertEqual("unavailable", requests[0].status.value)
        self.assertIn("GENERATOR_HANDLER_UNAVAILABLE", requests[0].requirements)

    def test_repair_unavailable_when_source_layout_required(self) -> None:
        crop = replace(
            artifact("crop"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(regenerable=True, requires_live_layout=True),
        )
        source = session(artifacts={"crop": crop})

        request = ArtifactRepairService().build_repair_requests(source)[0]

        self.assertEqual("unavailable", request.status.value)
        self.assertIn("SOURCE_LAYOUT_REQUIRED_FOR_REPAIR", request.requirements)

    def test_artifact_relink_updates_path_and_clears_missing_warning(self) -> None:
        service = ArtifactRepairService()
        source = session(artifacts={"crop": artifact("crop")})
        scanned, _result = service.scan_session(source, temp_paths())

        relinked = service.relink_artifact(scanned, "crop", "images/new.png")

        self.assertEqual("images/new.png", relinked.artifacts["crop"].relative_path)
        self.assertEqual(ArtifactStatus.PRESENT, relinked.artifacts["crop"].status)
        self.assertFalse(relinked.warnings)

    def test_artifact_registry_round_trips_through_session_json(self) -> None:
        crop = replace(
            artifact("crop"),
            repair=ArtifactRepairMetadata(regenerable=True),
            dependency_signature="sig-1",
            content_hash="sha256:abc",
        )
        source = session(artifacts={"crop": crop})

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            (paths.folder / crop.relative_path).write_text("image", encoding="utf-8")
            SessionJsonStore().save(source, paths)
            loaded = SessionJsonStore().load(paths.folder)

        self.assertIn("crop", loaded.artifacts)
        self.assertEqual("sha256:abc", loaded.artifacts["crop"].content_hash)

    def test_repair_routes_to_registered_generator(self) -> None:
        def handler(_session, artifact_record, _paths):
            return replace(artifact_record, status=ArtifactStatus.PRESENT)

        registry = ArtifactGeneratorRegistry(
            (
                GeneratorRegistration(
                    "fake",
                    ("captured_site_image",),
                    handler=handler,
                ),
            )
        )
        crop = replace(
            artifact("crop"),
            type="captured_site_image",
            generator="fake",
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(regenerable=True),
        )
        source = session(artifacts={"crop": crop})

        repaired = ArtifactRepairService(generators=registry).repair_artifact(
            source,
            "crop",
            temp_paths(),
        )

        self.assertEqual(ArtifactStatus.PRESENT, repaired.artifacts["crop"].status)


if __name__ == "__main__":
    unittest.main()

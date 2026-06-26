import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    SourceLayoutContext,
)
from metrology_process_planner.workflows.artifacts import (
    ArtifactRepairService,
    built_in_generator_registry,
)
from tests.artifact_lifecycle_fixtures import session as artifact_session


class ArtifactLayoutGeneratorRequirementTests(unittest.TestCase):
    def test_layout_crop_registration_declares_live_layout_requirement(self) -> None:
        registry = built_in_generator_registry()
        registration = next(
            item for item in registry.registrations() if item.generator_id == "layout_crop"
        )

        self.assertTrue(registration.requires_live_layout)
        self.assertFalse(registration.can_run_headless)

    def test_layout_crop_repair_reports_source_layout_requirement_before_handler_gap(self) -> None:
        target = _layout_crop()
        source = artifact_session(artifacts={target.id: target})

        request = ArtifactRepairService().build_repair_requests(source)[0]

        self.assertEqual("unavailable", request.status.value)
        self.assertIn("SOURCE_LAYOUT_REQUIRED_FOR_REPAIR", request.requirements)
        self.assertNotIn("GENERATOR_HANDLER_UNAVAILABLE", request.requirements)

    def test_layout_crop_repair_reports_missing_handler_after_layout_is_bound(self) -> None:
        target = _layout_crop()
        source = replace(
            artifact_session(artifacts={target.id: target}),
            source_layout=SourceLayoutContext(layout_path="source.gds"),
        )

        request = ArtifactRepairService().build_repair_requests(source)[0]

        self.assertEqual("unavailable", request.status.value)
        self.assertIn("GENERATOR_HANDLER_UNAVAILABLE", request.requirements)
        self.assertNotIn("SOURCE_LAYOUT_REQUIRED_FOR_REPAIR", request.requirements)


def _layout_crop() -> ArtifactRecord:
    return ArtifactRecord(
        "crop-001",
        "captured_site_image",
        "Site crop",
        "images/cap-001.png",
        ArtifactOwnerRef("capture", "cap-001", "crop"),
        status=ArtifactStatus.MISSING,
        generator="layout_crop",
        repair=ArtifactRepairMetadata(regenerable=True),
    )


if __name__ == "__main__":
    unittest.main()

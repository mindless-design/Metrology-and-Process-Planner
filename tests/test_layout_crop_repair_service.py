import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.layout_crop_repair import layout_crop_repair_service
from metrology_process_planner.domains.session import (
    ArtifactRepairMetadata,
    ArtifactStatus,
    SourceLayoutContext,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from tests.artifact_lifecycle_fixtures import artifact, session


class LayoutCropRepairServiceTests(unittest.TestCase):
    def test_layout_crop_repair_exports_live_crop_and_marks_artifact_present(self) -> None:
        exporter = _FakeCropExporter()
        crop = replace(
            artifact("crop"),
            status=ArtifactStatus.MISSING,
            generator="layout_crop",
            repair=ArtifactRepairMetadata(regenerable=True),
        )
        source = replace(
            session(artifacts={"crop": crop}),
            source_layout=SourceLayoutContext(layout_path="source.gds"),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()

            repaired = layout_crop_repair_service(exporter).repair_artifact(
                source,
                "crop",
                paths,
            )
            output_exists = artifact_path_to_disk(
                paths.folder,
                repaired.artifacts["crop"].relative_path,
            ).exists()

        self.assertTrue(output_exists)
        self.assertEqual(ArtifactStatus.PRESENT, repaired.artifacts["crop"].status)
        self.assertEqual((0, 0, 5, 5), exporter.bounds)


class _FakeCropExporter:
    def __init__(self) -> None:
        self.bounds = None

    def export_image(self, bounds, destination):
        self.bounds = (bounds.left, bounds.bottom, bounds.right, bounds.top)
        destination.write_text("crop", encoding="utf-8")
        return None


if __name__ == "__main__":
    unittest.main()

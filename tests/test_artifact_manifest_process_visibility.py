import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.artifact_helpers import capture_crop_artifact
from tests.editor_render_fixtures import session_without_pending


class ArtifactManifestProcessVisibilityTests(unittest.TestCase):
    def test_recipe_free_manifest_export_hides_process_only_artifacts(self) -> None:
        services = build_app_services()
        visible = capture_crop_artifact()
        hidden = _process_artifact(ArtifactStatus.MISSING)
        session = replace(
            session_without_pending(),
            artifacts={visible.id: visible, hidden.id: hidden},
        )
        with TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.session_editor_controller.open_document(
                SessionDocumentBuilder().build(session),
                paths,
            )

            routed = services.command_router.route(CommandId.EXPORT_ARTIFACT_MANIFEST)

            manifest = json.loads(Path(routed.output_path).read_text(encoding="utf-8"))

        self.assertEqual("success", routed.status)
        self.assertIn(visible.id, manifest)
        self.assertNotIn(hidden.id, manifest)

    def test_bulk_missing_message_ignores_hidden_process_only_artifacts(self) -> None:
        services = build_app_services()
        hidden = _process_artifact(ArtifactStatus.MISSING)
        session = replace(session_without_pending(), artifacts={hidden.id: hidden})
        with TemporaryDirectory() as temp_dir:
            services.session_editor_controller.open_document(
                SessionDocumentBuilder().build(session),
                SessionPaths.for_folder(Path(temp_dir)),
            )

            routed = services.command_router.route(CommandId.REGENERATE_MISSING_ARTIFACTS)

        self.assertIn("0 candidate(s)", routed.message)


def _process_artifact(status: ArtifactStatus) -> ArtifactRecord:
    return ArtifactRecord(
        "legacy-process-output",
        "process_output",
        "Legacy Process Output",
        "process_outputs/legacy.json",
        ArtifactOwnerRef("capture", "cap-001", "stack_image"),
        status=status,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            requires_recipe=True,
            requires_solver=True,
        ),
    )


if __name__ == "__main__":
    unittest.main()

import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SessionModeId,
    SetupItemRecord,
    SetupState,
    WarningRecord,
)
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from tests.editor_render_fixtures import session


class SetupGuideBadgeTestsPart2(unittest.TestCase):
    def test_external_recipe_free_setup_cards_hide_process_artifact_badges(self) -> None:
        registry = _external_recipe_free_setup_registry()
        hidden = ArtifactRecord(
            "legacy-process-output",
            "process_output",
            "Legacy Process Output",
            "process_outputs/legacy.json",
            ArtifactOwnerRef("setup", "reference", "stack_image"),
            status=ArtifactStatus.MISSING,
        )
        source = replace(
            session(),
            mode=SessionModeId("external_setup"),
            artifacts={hidden.id: hidden},
            setup=SetupState(
                items=(
                    SetupItemRecord(
                        "reference",
                        "origin_reference_box_capture",
                        "Reference Image",
                        "complete",
                        artifact_refs={"stack": hidden.id},
                    ),
                )
            ),
        )

        stages = {
            stage.stage_id: stage
            for stage in SetupGuidePresenter(mode_registry=registry).build(source).stages
        }

        self.assertEqual("none", stages["reference"].artifact_badge)

    def test_external_recipe_free_setup_cards_hide_process_warning_ids(self) -> None:
        registry = _external_recipe_free_setup_registry()
        source = replace(
            session(),
            mode=SessionModeId("external_setup"),
            setup=SetupState(
                items=(
                    SetupItemRecord(
                        "alignment",
                        "alignment_box_capture",
                        "Alignment",
                        "warning",
                        warning_ids=("process-warning", "artifact-warning"),
                    ),
                )
            ),
            warnings=(
                WarningRecord(
                    "process-warning",
                    "Recipe missing",
                    source="process_context",
                    code="PROCESS_RECIPE_MISSING",
                ),
                WarningRecord("artifact-warning", "Artifact missing", code="ARTIFACT_MISSING"),
            ),
        )

        stages = {
            stage.stage_id: stage
            for stage in SetupGuidePresenter(mode_registry=registry).build(source).stages
        }

        self.assertEqual(1, stages["alignment"].warning_count)


def _external_recipe_free_setup_registry() -> ModeRegistry:
    return ModeRegistry((ModeDefinition("external_setup", "External Setup"),))

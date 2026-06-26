import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    SetupItemRecord,
    SetupState,
    WarningRecord,
)
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from tests.editor_render_fixtures import session


class SetupGuideBadgeTests(unittest.TestCase):
    def test_setup_cards_expose_requirement_badges(self) -> None:
        view_model = SetupGuidePresenter().build(session())
        stages = {stage.stage_id: stage for stage in view_model.stages}

        self.assertEqual("optional", stages["origin"].requirement_badge)
        self.assertEqual("optional", stages["alignment"].requirement_badge)
        self.assertEqual("required", stages["ready_for_capture"].requirement_badge)

    def test_setup_cards_expose_artifact_availability_badges(self) -> None:
        source = replace(
            session(),
            setup=SetupState(
                items=(
                    SetupItemRecord(
                        "reference",
                        "origin_reference_box_capture",
                        "Reference Image",
                        "complete",
                        artifact_refs={"crop": "capture-cap-001-crop"},
                    ),
                    SetupItemRecord(
                        "missing-reference",
                        "alignment_box_capture",
                        "Missing Reference",
                        "warning",
                        artifact_refs={"crop": "missing-artifact"},
                    ),
                )
            ),
        )

        stages = {stage.stage_id: stage for stage in SetupGuidePresenter().build(source).stages}

        self.assertEqual("present", stages["reference"].artifact_badge)
        self.assertEqual("missing", stages["missing-reference"].artifact_badge)

    def test_setup_cards_hide_process_only_artifact_badges_for_recipe_free_modes(self) -> None:
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
            artifacts={"legacy-process-output": hidden},
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

        stages = {stage.stage_id: stage for stage in SetupGuidePresenter().build(source).stages}

        self.assertEqual("none", stages["reference"].artifact_badge)

    def test_setup_cards_hide_process_warning_ids_for_recipe_free_modes(self) -> None:
        source = replace(
            session(),
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

        stages = {stage.stage_id: stage for stage in SetupGuidePresenter().build(source).stages}

        self.assertEqual(1, stages["alignment"].warning_count)


def _external_recipe_free_setup_registry() -> ModeRegistry:
    return ModeRegistry((ModeDefinition("external_setup", "External Setup"),))

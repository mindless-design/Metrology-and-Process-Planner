import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import SetupItemRecord, SetupState
from metrology_process_planner.ui.setup_guide import SetupGuidePresenter
from tests.editor_render_fixtures import session


class SetupGuideBadgeTests(unittest.TestCase):
    def test_setup_cards_expose_requirement_badges(self) -> None:
        view_model = SetupGuidePresenter().build(session())
        stages = {stage.stage_id: stage for stage in view_model.stages}

        self.assertEqual("optional", stages["origin"].requirement_badge)
        self.assertEqual("optional", stages["alignment"].requirement_badge)
        self.assertEqual("required", stages["complete"].requirement_badge)

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


if __name__ == "__main__":
    unittest.main()

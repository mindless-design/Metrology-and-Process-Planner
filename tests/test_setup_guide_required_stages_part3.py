import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.domains.session import (
    SessionMode,
    SetupItemRecord,
    SetupState,
    built_in_mode_registry,
)
from metrology_process_planner.persistence.json_store import SessionJsonStore
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.setup_guide_state import SetupGuideStateMachine
from tests.editor_render_fixtures import session


def _complete_item(
    item_id: str,
    *,
    item_type: str = "alignment_box_capture",
    label: str = "Optical Alignment Mark",
) -> SetupItemRecord:
    return SetupItemRecord(
        item_id,
        item_type,
        label,
        "complete",
        metadata={"required": True},
    )

if __name__ == "__main__":
    unittest.main()


class SetupGuideRequiredStageTestsPart3(unittest.TestCase):
    def test_cdsem_partial_setup_still_shows_required_sem_alignment(self) -> None:
        services = build_app_services()
        source = replace(
            session(),
            mode=SessionMode.CDSEM_CAPTURE,
            setup=SetupState(items=(_complete_item("optical_alignment"),)),
        )
        services.setup_guide_controller.set_active_session(source)

        opened = services.setup_guide_controller.open_current()
        stages = {stage.stage_id: stage for stage in opened.view_model.stages}

        self.assertEqual("complete", stages["optical_alignment"].status)
        self.assertEqual("active", stages["sem_alignment"].status)
        self.assertEqual("required", stages["sem_alignment"].requirement_badge)
        self.assertEqual("StartSemAlignmentCapture", stages["sem_alignment"].primary_action)

    def test_setup_readiness_survives_save_and_reopen_for_optical_and_cdsem(self) -> None:
        registry = built_in_mode_registry()
        store = SessionJsonStore()

        for mode, items in _readiness_cases():
            with self.subTest(mode=mode.value), TemporaryDirectory() as temp_dir:
                paths = SessionPaths.for_folder(Path(temp_dir))
                source = replace(
                    session(),
                    mode=mode,
                    setup=SetupState(is_capture_ready=True, items=items),
                )

                store.save(source, paths)
                loaded = store.load(paths.folder)
                definition = registry.definition(loaded.mode.value)
                snapshot = SetupGuideStateMachine().evaluate(loaded, definition, registry)

                self.assertTrue(loaded.setup.is_capture_ready)
                _assert_snapshot_ready(self, snapshot)


def _readiness_cases():
    cdsem_items = (
        _complete_item("optical_alignment"),
        _complete_item(
            "sem_alignment",
            item_type="sem_alignment_box_capture",
            label="SEM Alignment Mark",
        ),
    )
    return (
        (SessionMode.OPTICAL_METROLOGY, (_complete_item("optical_alignment"),)),
        (SessionMode.CDSEM_MEASUREMENT, cdsem_items),
        (SessionMode.CDSEM_PLANNING, cdsem_items),
    )


def _assert_snapshot_ready(test_case, snapshot) -> None:
    test_case.assertEqual("setup_ready", snapshot.state.value)
    test_case.assertEqual("ready_for_capture", snapshot.active_stage_id)
    test_case.assertEqual(
        (),
        tuple(stage.stage_id for stage in snapshot.stages if stage.status.value == "blocked"),
    )

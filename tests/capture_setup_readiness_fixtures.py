from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import (
    ModeCapabilities,
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SessionRecord,
    SetupDefinition,
    SetupItemRecord,
)
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext


def drag_box(source: SessionRecord, mode_registry: ModeRegistry | None = None):
    engine = CanvasInteractionEngine(mode_registry=mode_registry)
    context = engine.arm_box_capture(InteractionContext())
    started = engine.start_drag(source, context, Point(0, 0), shift_pressed=True)
    result = engine.release_drag(started.session, started.context, Point(5, 5), True)
    return result.session, result


def session(mode: SessionMode) -> SessionRecord:
    return SessionRecord(
        id="session-setup-readiness",
        name="Setup Readiness",
        mode=mode,
        created_at="2026-06-25T00:00:00Z",
        updated_at="2026-06-25T00:00:00Z",
    )


def complete_alignment(item_id: str) -> SetupItemRecord:
    item_type = "sem_alignment_box_capture" if item_id == "sem_alignment" else (
        "alignment_box_capture"
    )
    label = "SEM Alignment Mark" if item_id == "sem_alignment" else "Optical Alignment Mark"
    return SetupItemRecord(
        item_id,
        item_type,
        label,
        "complete",
        metadata={"required": True},
    )


def external_setup_registry() -> ModeRegistry:
    return ModeRegistry(
        (
            ModeDefinition(
                "external_setup",
                "External Setup",
                family="metrology",
                capabilities=ModeCapabilities(uses_setup_guide=True),
                setup=SetupDefinition(
                    required=True,
                    can_skip=False,
                    stage_types=("required_optical_alignment_mark",),
                ),
            ),
        )
    )

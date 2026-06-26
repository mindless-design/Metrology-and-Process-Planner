"""Process-flow scene helpers for cross-section rendering."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.process import Material, ProcessFrame, SolverResult
from metrology_process_planner.rendering.cross_section.models import RenderIntent, RenderProfile
from metrology_process_planner.rendering.cross_section.scene_models import CrossSectionSceneModel


def build_process_flow_scenes(
    solver_result: SolverResult,
    profile: RenderProfile,
    materials: tuple[Material, ...] = (),
    emit_unchanged: bool = False,
) -> tuple[CrossSectionSceneModel, ...]:
    """Build process-flow frame scenes, skipping unchanged stack signatures by default."""

    from metrology_process_planner.rendering.cross_section.pipeline import (
        build_cross_section_scene,
    )

    scenes: list[CrossSectionSceneModel] = []
    previous_signature = ""
    for index, frame in enumerate(solver_result.frames):
        signature = _frame_signature(frame)
        if signature == previous_signature and not emit_unchanged:
            continue
        previous_signature = signature
        single = replace(solver_result, frames=(frame,))
        intent = RenderIntent.from_profile(
            profile,
            selected_process_step_id=frame.step_id,
            highlight_policy="current_step_change",
        )
        scenes.append(
            build_cross_section_scene(
                single,
                profile,
                intent,
                materials,
                f"process-flow-frame-{index + 1:03d}",
                frame.title,
            )
        )
    return tuple(scenes)


def _frame_signature(frame: ProcessFrame) -> str:
    return "|".join(
        f"{column.x}:{','.join(interval.material_id for interval in column.intervals)}"
        for column in frame.profile.columns
    )

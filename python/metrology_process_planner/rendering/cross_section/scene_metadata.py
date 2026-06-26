"""Cross-section scene identity and metadata helpers."""

from __future__ import annotations

from metrology_process_planner.domains.process import ProcessFrame
from metrology_process_planner.rendering.cross_section.models import RenderIntent, RenderProfile


def unique_warning_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    """Return warning codes with original order preserved."""

    return tuple(dict.fromkeys(values))


def scene_title(frame: ProcessFrame, profile: RenderProfile) -> str:
    """Return the default title for a frame/profile pair."""

    if profile.render_mode_id == "process_flow_frame":
        step_number = getattr(frame, "step_index", None)
        step_prefix = f"Step {int(step_number) + 1:02d} - " if step_number is not None else ""
        return f"{step_prefix}{frame.title or profile.display_name}"
    return frame.title or profile.display_name


def source_refs(
    frame: ProcessFrame,
    profile: RenderProfile,
    intent: RenderIntent,
) -> dict[str, str]:
    """Return public provenance for renderer/report consumers."""

    return {
        "selected_step_id": intent.selected_process_step_id or "",
        "render_profile_id": profile.profile_id,
        "render_mode_id": profile.render_mode_id,
        "source_step_id": frame.step_id,
        "source_step_name": frame.title,
    }

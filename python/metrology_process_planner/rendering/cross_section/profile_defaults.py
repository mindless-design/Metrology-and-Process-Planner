"""Default render-profile resolution for process-aware visual outputs."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.rendering.cross_section.models import RenderProfile
from metrology_process_planner.rendering.cross_section.profile_catalog import (
    built_in_render_profile,
)

PROCESS_ROLE_RENDER_PROFILES: dict[str, str] = {
    "profile_image": "profilometry_surface_profile",
    "line_profile": "profilometry_surface_profile",
    "profilometry": "profilometry_surface_profile",
    "stack_image": "point_stack_schematic",
    "point_stack": "point_stack_schematic",
    "point_stack_table": "point_stack_schematic",
    "ellipsometry": "point_stack_schematic",
    "full_stack_compressed_image": "fib_full_stack_compressed",
    "fib_full_stack": "fib_full_stack_compressed",
    "fib": "fib_full_stack_compressed",
    "process_flow_frame": "process_flow_frame",
    "process_flow": "process_flow_frame",
    "cross_section_image": "physical_cross_section",
}

FALLBACK_RENDER_PROFILE_ID = "physical_cross_section"


@dataclass(frozen=True)
class RenderProfileResolution:
    """Resolved render profile plus any clarity/reliability warnings."""

    profile: RenderProfile
    profile_id: str
    requested_profile_id: str
    warnings: tuple[str, ...] = ()


def default_render_profile_id(output_type_or_role: str) -> str:
    """Return the default profile id for a process output type or artifact role."""

    return PROCESS_ROLE_RENDER_PROFILES.get(output_type_or_role, FALLBACK_RENDER_PROFILE_ID)


def resolve_render_profile(
    output_type_or_role: str,
    requested_profile_id: str = "",
) -> RenderProfileResolution:
    """Resolve a profile and downgrade missing choices to a warning-backed fallback."""

    profile_id = requested_profile_id or default_render_profile_id(output_type_or_role)
    try:
        return RenderProfileResolution(
            built_in_render_profile(profile_id),
            profile_id,
            requested_profile_id,
        )
    except KeyError:
        fallback = built_in_render_profile(FALLBACK_RENDER_PROFILE_ID)
        return RenderProfileResolution(
            fallback,
            fallback.profile_id,
            requested_profile_id or profile_id,
            ("RENDER_PROFILE_MISSING",),
        )

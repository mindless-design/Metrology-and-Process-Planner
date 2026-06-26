"""Mode-aware artifact visibility helpers."""

from __future__ import annotations

import re

from metrology_process_planner.domains.artifacts.artifact_registry import ArtifactRecord
from metrology_process_planner.domains.modes.mode_registry import ModeRegistry
from metrology_process_planner.domains.session.record import SessionRecord
from metrology_process_planner.domains.warnings.warning_visibility import session_is_process_aware

_PROCESS_ARTIFACT_TYPES_AND_ROLES = {
    "cross_section",
    "cross_section_image",
    "film_thickness_summary",
    "full_stack_compressed",
    "full_stack_compressed_image",
    "point_stack",
    "point_stack_table",
    "process_flow_frame",
    "process_output",
    "profile_image",
    "stack_image",
}


def artifact_visible_for_session(
    session: SessionRecord,
    artifact: ArtifactRecord,
    mode_registry: ModeRegistry | None = None,
) -> bool:
    """Return whether an artifact belongs in normal mode-scoped surfaces."""

    return _session_is_process_aware(session, mode_registry) or not is_process_artifact(artifact)


def is_process_artifact(artifact: ArtifactRecord) -> bool:
    """Return whether an artifact depends on process recipe or solver context."""

    repair = artifact.repair
    artifact_type = _policy_key(artifact.type)
    owner_role = _policy_key(artifact.owner.role)
    owner_type = _policy_key(artifact.owner.owner_type)
    return (
        artifact_type in _PROCESS_ARTIFACT_TYPES_AND_ROLES
        or _role_stem(artifact_type) in _PROCESS_ARTIFACT_TYPES_AND_ROLES
        or owner_type == "process_output"
        or owner_role in _PROCESS_ARTIFACT_TYPES_AND_ROLES
        or _role_stem(owner_role) in _PROCESS_ARTIFACT_TYPES_AND_ROLES
        or repair.repair_action == "regenerate_process_output"
        or repair.requires_recipe
        or repair.requires_solver
    )


def _role_stem(role: str) -> str:
    for suffix in ("_spec", "_svg", "_png", "_image"):
        if role.endswith(suffix):
            return role[: -len(suffix)]
    return role


def _policy_key(value: str) -> str:
    camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value))
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", camel_split).strip("_").lower()
    return re.sub(r"_+", "_", normalized)


def _session_is_process_aware(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    if mode_registry is None:
        return session_is_process_aware(session)
    mode = mode_registry.definition(session.mode.value)
    return (
        mode.family == "process_aware"
        or mode.capabilities.supports_process_solver
        or mode.process.recipe_policy not in {"forbidden", "optional_hidden"}
    )

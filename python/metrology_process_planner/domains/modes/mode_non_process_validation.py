"""Validation helpers for recipe-free mode contracts."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.modes.mode_non_process_helpers import (
    is_report_only_compatibility_mode,
    leaked_policy_values,
    process_artifact_outputs,
    process_report_sections,
)


def non_process_contract_warnings(definition: Any) -> tuple[str, ...]:
    """Return warnings when a non-process mode leaks recipe or solver concepts."""

    if definition.family == "process_aware":
        return ()
    warnings: list[str] = []
    if definition.process.recipe_policy not in {"forbidden", "optional_hidden"}:
        warnings.append(
            f"Mode {definition.mode_id or '<missing>'}: non-process modes must hide recipe setup.",
        )
    warnings.extend(_solver_warnings(definition))
    warnings.extend(_artifact_warnings(definition))
    warnings.extend(_editor_warnings(definition))
    warnings.extend(_setup_report_warnings(definition))
    return tuple(warnings)


def _solver_warnings(definition: Any) -> tuple[str, ...]:
    warnings: list[str] = []
    if definition.process.solver_operation not in {"", "none"}:
        warnings.append(
            f"Mode {definition.mode_id or '<missing>'}: "
            "non-process modes must not declare solver operation."
        )
    if definition.process.render_profile:
        warnings.append(
            f"Mode {definition.mode_id or '<missing>'}: "
            "non-process modes must not declare render profile."
        )
    if definition.capabilities.supports_process_solver:
        warnings.append(
            f"Mode {definition.mode_id or '<missing>'}: "
            "non-process modes must not support process solver."
        )
    return tuple(warnings)


def _artifact_warnings(definition: Any) -> tuple[str, ...]:
    process_outputs = process_artifact_outputs(definition)
    if not process_outputs:
        return ()
    return (
        f"Mode {definition.mode_id or '<missing>'}: "
        "non-process modes must not declare process outputs: "
        f"{', '.join(process_outputs)}.",
    )


def _editor_warnings(definition: Any) -> tuple[str, ...]:
    return (
        *_process_context_visibility_warnings(definition),
        *_leaked_editor_group_warnings(definition),
        *_leaked_editor_action_warnings(definition),
        *_leaked_editor_preview_warnings(definition),
    )


def _process_context_visibility_warnings(definition: Any) -> tuple[str, ...]:
    if not definition.editor.process_context_visible:
        return ()
    return (
        f"Mode {definition.mode_id or '<missing>'}: "
        "non-process editor must hide process context.",
    )


def _leaked_editor_group_warnings(definition: Any) -> tuple[str, ...]:
    leaked_groups = leaked_policy_values(
        definition.editor.navigator_groups,
        _PROCESS_EDITOR_GROUPS,
    )
    if not leaked_groups:
        return ()
    return (
        f"Mode {definition.mode_id or '<missing>'}: non-process editor leaks process groups: "
        f"{', '.join(sorted(leaked_groups))}.",
    )


def _leaked_editor_action_warnings(definition: Any) -> tuple[str, ...]:
    leaked_actions = leaked_policy_values(
        definition.editor.actions,
        _PROCESS_EDITOR_ACTIONS,
    )
    if not leaked_actions:
        return ()
    return (
        f"Mode {definition.mode_id or '<missing>'}: non-process editor leaks process actions: "
        f"{', '.join(sorted(leaked_actions))}.",
    )


def _leaked_editor_preview_warnings(definition: Any) -> tuple[str, ...]:
    leaked_previews = leaked_policy_values(
        definition.editor.preview_modes,
        _PROCESS_PREVIEW_MODES,
    )


    if not leaked_previews:
        return ()
    return (
        f"Mode {definition.mode_id or '<missing>'}: non-process editor leaks process previews: "
        f"{', '.join(sorted(leaked_previews))}.",
    )


def _setup_report_warnings(definition: Any) -> tuple[str, ...]:
    return (
        *_recipe_stage_warnings(definition),
        *_report_section_warnings(definition),
    )


def _recipe_stage_warnings(definition: Any) -> tuple[str, ...]:
    recipe_stages = leaked_policy_values(
        definition.setup.stage_types,
        _RECIPE_SETUP_STAGES,
    )
    if not recipe_stages:
        return ()
    return (
        f"Mode {definition.mode_id or '<missing>'}: "
        "non-process setup must not include recipe stages: "
        f"{', '.join(sorted(recipe_stages))}.",
    )


def _report_section_warnings(definition: Any) -> tuple[str, ...]:
    leaked_sections = process_report_sections(definition.reporting.sections)
    if not leaked_sections or is_report_only_compatibility_mode(definition):
        return ()
    return (
        f"Mode {definition.mode_id or '<missing>'}: "
        "non-process reports must not declare process sections: "
        f"{', '.join(leaked_sections)}.",
    )


_PROCESS_PREVIEW_MODES = {
    "cross_section_image",
    "full_stack_compressed_image",
    "film_thickness_summary",
    "point_stack_table",
    "profile_image",
    "stack_image",
}

_PROCESS_EDITOR_GROUPS = {
    "cross_section",
    "cross_sections",
    "process_context",
    "process_outputs",
    "process_report",
    "process_summary",
    "profile_image",
    "profile_preview",
    "stack_image",
    "stack_preview",
}

_PROCESS_EDITOR_ACTIONS = {
    "attach_recipe",
    "detach_recipe",
    "regenerate_process_output",
    "validate_process_context",
}

_RECIPE_SETUP_STAGES = {
    "attach_recipe",
    "process_recipe",
    "recipe",
    "recipe_context",
    "recipe_setup",
    "validate_process_context",
}

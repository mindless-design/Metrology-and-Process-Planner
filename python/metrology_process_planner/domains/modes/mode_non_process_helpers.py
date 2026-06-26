"""Policy helpers for validating recipe-free modes."""

from __future__ import annotations

import re
from typing import Any


def is_report_only_compatibility_mode(definition: Any) -> bool:
    """Return whether a hidden legacy mode is report-only compatible."""

    extensions = definition.extensions or {}
    return bool(
        not definition.visible
        and extensions.get("mode_scope") == "report_only_compatibility"
        and _has_no_process_requirements(definition)
        and not _uses_solver_or_canvas(definition)
    )


def process_report_sections(sections: tuple[str, ...]) -> tuple[str, ...]:
    """Return report sections that expose process-specific content."""

    return tuple(
        section
        for section in sections
        if _policy_key(section).startswith("process")
        or _policy_key(section) in _PROCESS_REPORT_SECTIONS
    )


def process_artifact_outputs(definition: Any) -> tuple[str, ...]:
    """Return declared capture-save outputs that look process-specific."""

    outputs = []
    for item in definition.artifacts.on_capture_save:
        artifact_type = item.artifact_type
        role = item.role
        artifact_key = _policy_key(artifact_type)
        role_key = _policy_key(role)
        if _is_process_artifact_key(artifact_key) or _is_process_artifact_key(role_key):
            outputs.append(role or artifact_type)
    return tuple(outputs)


def leaked_policy_values(values: tuple[str, ...], blocked: set[str]) -> tuple[str, ...]:
    """Return configured values whose normalized keys are blocked."""

    return tuple(value for value in values if _policy_key(value) in blocked)


def _has_no_process_requirements(definition: Any) -> bool:
    return bool(
        definition.process.recipe_policy == "forbidden"
        and definition.process.solver_operation in {"", "none"}
    )


def _uses_solver_or_canvas(definition: Any) -> bool:
    return bool(
        definition.capabilities.supports_process_solver
        or definition.capabilities.uses_canvas_objects
    )


def _is_process_artifact_key(key: str) -> bool:
    stem = _artifact_role_stem(key)
    return (
        key in _PROCESS_ARTIFACT_NAMES
        or stem in _PROCESS_ARTIFACT_NAMES
        or key.startswith("process_output_")
        or stem.startswith("process_output_")
    )


def _policy_key(value: str) -> str:
    camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value))
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", camel_split).strip("_").lower()
    return re.sub(r"_+", "_", normalized)


def _artifact_role_stem(role: str) -> str:
    for suffix in ("_spec", "_svg", "_png", "_image", "_manifest", "_json", "_csv"):
        if role.endswith(suffix):
            return role[: -len(suffix)]
    return role


_PROCESS_PREVIEW_MODES = {
    "cross_section_image",
    "full_stack_compressed_image",
    "film_thickness_summary",
    "point_stack_table",
    "profile_image",
    "stack_image",
}

_PROCESS_REPORT_SECTIONS = {
    "cross_section",
    "cross_section_gallery",
    "film_thickness_summary",
    "full_stack_compressed",
    "point_stack",
    "process_context",
    "process_report",
    "process_summary",
    "profile_summary",
    "stack_summary",
}

_PROCESS_ARTIFACT_NAMES = _PROCESS_PREVIEW_MODES.union(_PROCESS_REPORT_SECTIONS).union(
    {
        "process_flow_frame",
        "process_output",
    }
)

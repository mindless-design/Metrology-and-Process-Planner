"""Process-output regeneration for process-aware captures."""

from __future__ import annotations

import json
from pathlib import Path

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.domains.session import CaptureRecord, SessionRecord, WarningRecord
from metrology_process_planner.workflows.process_capture_extensions import (
    is_process_aware_capture,
)
from metrology_process_planner.workflows.process_context_models import (
    RegenerateProcessOutputsCommand,
)
from metrology_process_planner.workflows.process_context_support import (
    process_warning,
    with_warnings,
)
from metrology_process_planner.workflows.process_output_service import ProcessOutputService
from metrology_process_planner.workflows.process_regeneration_execution import (
    solve_capture_process_output,
    solve_targets,
)

__all__ = [
    "regenerate_capture_outputs",
    "solve_capture_process_output",
]


def regenerate_capture_outputs(
    session: SessionRecord,
    command: RegenerateProcessOutputsCommand,
) -> tuple[SessionRecord, tuple[WarningRecord, ...], str, str]:
    """Regenerate process outputs for one capture or all process-aware captures."""

    captures = _target_captures(session, command.owner_id)
    if not captures:
        return _no_target_result(session, command.owner_id)
    recipe_result = _recipe(session)
    if isinstance(recipe_result, WarningRecord):
        return _recipe_unavailable_result(session, captures, recipe_result)
    if session.process_context.solver_backend != "HybridCrossSectionSolver":
        return _solver_unavailable_result(session, command.owner_id)
    return solve_targets(session, captures, recipe_result)


def _target_captures(session: SessionRecord, owner_id: str) -> tuple[CaptureRecord, ...]:
    captures = tuple(capture for capture in session.captures if is_process_aware_capture(capture))
    if owner_id:
        return tuple(capture for capture in captures if capture.id == owner_id)
    return captures


def _no_target_result(
    session: SessionRecord,
    owner_id: str,
) -> tuple[SessionRecord, tuple[WarningRecord, ...], str, str]:
    warning = process_warning(
        "PROCESS_OUTPUT_REGENERATION_FAILED",
        "No process-aware capture was found for regeneration.",
        "Select a saved process-aware capture.",
        owner_id,
    )
    result = with_warnings(session, (warning,), "warning", "No process output target.")
    return result.session, result.warnings, result.status, result.message


def _recipe_unavailable_result(
    session: SessionRecord,
    captures: tuple[CaptureRecord, ...],
    warning: WarningRecord,
) -> tuple[SessionRecord, tuple[WarningRecord, ...], str, str]:
    session = ProcessOutputService().ensure_placeholder_outputs(session, captures, (warning,))
    result = with_warnings(session, (warning,), "warning", "Recipe unavailable.")
    return result.session, result.warnings, result.status, result.message


def _solver_unavailable_result(
    session: SessionRecord,
    owner_id: str,
) -> tuple[SessionRecord, tuple[WarningRecord, ...], str, str]:
    warning = process_warning(
        "SOLVER_BACKEND_UNAVAILABLE",
        "HybridCrossSectionSolver is not configured for this session.",
        "Configure HybridCrossSectionSolver before regenerating process outputs.",
        owner_id,
    )
    result = with_warnings(session, (warning,), "warning", "Solver unavailable.")
    return result.session, result.warnings, result.status, result.message


def _recipe(session: SessionRecord) -> ProcessRecipe | WarningRecord:
    context = session.process_context
    if not context.recipe_path:
        return process_warning(
            "PROCESS_RECIPE_MISSING",
            "No process recipe is attached.",
            "Attach a process recipe and regenerate process outputs.",
        )
    path = Path(context.recipe_path)
    if not path.exists():
        return process_warning(
            "PROCESS_RECIPE_FILE_NOT_FOUND",
            f"Recipe file was not found: {context.recipe_path}",
            "Attach an existing recipe file.",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ProcessRecipe.from_dict(payload)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return process_warning(
            "PROCESS_RECIPE_PARSE_FAILED",
            f"Recipe could not be parsed for regeneration: {exc}",
            "Choose a valid process recipe JSON file.",
        )

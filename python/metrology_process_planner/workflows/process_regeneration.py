"""Process-output regeneration for process-aware captures."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.process import (
    HybridCrossSectionSolver,
    ProcessRecipe,
    SolverInput,
    SolverOptions,
)
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    CaptureRecord,
    SessionRecord,
    WarningRecord,
)
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
from metrology_process_planner.workflows.process_regeneration_records import (
    failed_output,
    mark_output_artifacts,
    ready_output,
    solver_operation,
    upsert_output,
)


def regenerate_capture_outputs(
    session: SessionRecord,
    command: RegenerateProcessOutputsCommand,
) -> tuple[SessionRecord, tuple[WarningRecord, ...], str, str]:
    """Regenerate process outputs for one capture or all process-aware captures."""

    captures = _target_captures(session, command.owner_id)
    if not captures:
        warning = process_warning(
            "PROCESS_OUTPUT_REGENERATION_FAILED",
            "No process-aware capture was found for regeneration.",
            "Select a saved process-aware capture.",
            command.owner_id,
        )
        result = with_warnings(session, (warning,), "warning", "No process output target.")
        return result.session, result.warnings, result.status, result.message
    recipe_result = _recipe(session)
    if isinstance(recipe_result, WarningRecord):
        result = with_warnings(session, (recipe_result,), "warning", "Recipe unavailable.")
        return result.session, result.warnings, result.status, result.message
    if session.process_context.solver_backend != "HybridCrossSectionSolver":
        warning = process_warning(
            "SOLVER_BACKEND_UNAVAILABLE",
            "HybridCrossSectionSolver is not configured for this session.",
            "Configure HybridCrossSectionSolver before regenerating process outputs.",
            command.owner_id,
        )
        result = with_warnings(session, (warning,), "warning", "Solver unavailable.")
        return result.session, result.warnings, result.status, result.message
    return _solve_targets(session, captures, recipe_result)


def _target_captures(session: SessionRecord, owner_id: str) -> tuple[CaptureRecord, ...]:
    captures = tuple(capture for capture in session.captures if is_process_aware_capture(capture))
    if owner_id:
        return tuple(capture for capture in captures if capture.id == owner_id)
    return captures


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


def _solve_targets(
    session: SessionRecord,
    captures: tuple[CaptureRecord, ...],
    recipe: ProcessRecipe,
) -> tuple[SessionRecord, tuple[WarningRecord, ...], str, str]:
    warnings: list[WarningRecord] = []
    outputs = list(session.process_outputs)
    artifacts = dict(session.artifacts or {})
    for capture in captures:
        try:
            solver_result = HybridCrossSectionSolver().solve(_solver_input(capture, recipe))
        except ValueError as exc:
            warning = process_warning(
                "PROCESS_OUTPUT_REGENERATION_FAILED",
                f"Process output regeneration failed: {exc}",
                "Review the process recipe and capture geometry.",
                capture.id,
            )
            warnings.append(warning)
            outputs = upsert_output(outputs, failed_output(capture, (warning.id,)))
            artifacts = mark_output_artifacts(
                artifacts,
                capture,
                ArtifactStatus.FAILED,
                warning.id,
            )
            continue
        output = ready_output(capture, solver_result)
        outputs = upsert_output(outputs, output)
        artifacts = mark_output_artifacts(artifacts, capture, ArtifactStatus.STALE, "")
    session = replace(session, process_outputs=tuple(outputs), artifacts=artifacts)
    if warnings:
        result = with_warnings(session, tuple(warnings), "warning", "Regenerated with warnings.")
        return result.session, result.warnings, result.status, result.message
    return session, (), "success", "Regenerated process outputs."


def _solver_input(capture: CaptureRecord, recipe: ProcessRecipe) -> SolverInput:
    operation = solver_operation(capture)
    bounds = capture.geometry.bounds
    x_min = bounds.left if bounds is not None else 0.0
    x_max = bounds.right if bounds is not None else 10.0
    options = SolverOptions(x_min=x_min, x_max=x_max, sample_count=101)
    feature = capture.geometry.features[0] if capture.geometry.features else {}
    geometry = dict(feature.get("geometry", {}))
    if operation == "point_stack":
        point = dict(geometry.get("point", {}))
        options = replace(options, point_sample_xs=(float(point.get("x", (x_min + x_max) / 2)),))
    if operation == "line_profile":
        start = dict(geometry.get("start", {}))
        end = dict(geometry.get("end", {}))
        start_x = float(start.get("x", x_min))
        end_x = float(end.get("x", x_max))
        options = replace(
            options,
            cutline_x_min=min(start_x, end_x),
            cutline_x_max=max(start_x, end_x),
        )
    return SolverInput(recipe, options)

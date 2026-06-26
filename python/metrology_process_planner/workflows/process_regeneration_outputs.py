"""Process-output record and capture-extension builders."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.process import SolverResult
from metrology_process_planner.domains.session import CaptureRecord, ProcessOutputRecord
from metrology_process_planner.workflows.process_output_requests import ProcessOutputRequest
from metrology_process_planner.workflows.process_regeneration_records import existing_output
from metrology_process_planner.workflows.process_regeneration_summary import (
    result_metadata,
    result_summary,
)


def ready_output(
    capture: CaptureRecord,
    request: ProcessOutputRequest,
    result: SolverResult,
    refs: dict[str, str],
    solver_result_id: str,
) -> ProcessOutputRecord:
    """Return a ready canonical process-output record."""

    output = existing_output(capture)
    return ProcessOutputRecord(
        output.id,
        output.label,
        request.operation,
        status="ready",
        artifact_refs={**dict(output.artifact_refs or {}), **refs},
        metadata={
            **dict(output.metadata or {}),
            **result_metadata(result),
            "solver_operation": request.operation,
            "render_profile": request.render_profile,
            "process_window_variant": request.process_window_variant,
            "solver_result_id": solver_result_id,
        },
        extensions={**dict(output.extensions or {}), "solver_result": result_summary(result)},
        warning_ids=(),
    )


def capture_with_process_output(
    capture: CaptureRecord,
    request: ProcessOutputRequest,
    refs: dict[str, str],
    solver_result_id: str,
    warning_ids: tuple[str, ...],
    solver_result: SolverResult | None,
    status: str,
) -> CaptureRecord:
    """Return a capture updated with process-output extension metadata."""

    extensions = dict(capture.extensions or {})
    key = _extension_key(request.operation)
    current = dict(extensions.get(key, {})) if isinstance(extensions.get(key), dict) else {}
    current.update(_process_output_extension(request, refs, solver_result_id, warning_ids, status))
    current.update(_operation_extension(request.operation, solver_result))
    extensions[key] = current
    return replace(
        capture,
        artifact_refs={**dict(capture.artifact_refs or {}), **refs},
        extensions=extensions,
        warning_ids=warning_ids,
    )


def _process_output_extension(
    request: ProcessOutputRequest,
    refs: dict[str, str],
    solver_result_id: str,
    warning_ids: tuple[str, ...],
    status: str,
) -> dict[str, object]:
    return {
        "process_context_ref": "process_context.active",
        "solver_request": {
            "operation": request.operation,
            "process_window_variant": request.process_window_variant,
            "render_profile": request.render_profile,
        },
        "solver_result_id": solver_result_id,
        "artifact_refs": refs,
        "warning_ids": list(warning_ids),
        "status": status,
    }


def _operation_extension(operation: str, result: SolverResult | None) -> dict[str, object]:
    if operation == "point_stack":
        return {"point_stack": _point_stack_rows(result)}
    if operation == "line_profile":
        return {"outputs": _profile_outputs(result)}
    if operation == "full_stack_compressed":
        return {"compression_metadata": {}}
    if operation == "process_flow_frames":
        return {"frame_sequence": _frame_sequence(result)}
    return {}


def _extension_key(operation: str) -> str:
    if operation == "point_stack":
        return "ellipsometry"
    if operation == "line_profile":
        return "profilometry"
    if operation == "full_stack_compressed":
        return "fib_cut"
    if operation == "process_flow_frames":
        return "process_flow"
    return "process_output"


def _point_stack_rows(result: SolverResult | None) -> list[dict[str, object]]:
    if result is None or not result.point_samples:
        return []
    material_names = {
        str(item.get("id", "")): str(item.get("name", item.get("id", "")))
        for item in result.material_metadata
    }
    return [
        {
            "order": order,
            "material_id": interval.material_id,
            "material_name": material_names.get(interval.material_id, interval.material_id),
            "thickness": max(0.0, interval.z_max - interval.z_min),
            "units": result.units,
            "visible": True,
        }
        for order, interval in enumerate(result.point_samples[0].intervals, start=1)
    ]


def _profile_outputs(result: SolverResult | None) -> dict[str, object]:
    if result is None:
        return {"stack_change_windows": [], "step_heights": []}
    heights = [sample.intervals[-1].z_max for sample in result.cutline_samples if sample.intervals]
    step_heights = []
    if heights:
        step_heights.append(
            {"min": min(heights), "max": max(heights), "delta": max(heights) - min(heights)}
        )
    return {"stack_change_windows": [], "step_heights": step_heights}


def _frame_sequence(result: SolverResult | None) -> list[dict[str, object]]:
    if result is None:
        return []
    return [
        {
            "frame_id": frame.frame_id,
            "step_id": frame.step_id,
            "step_name": frame.step_name,
            "stack_signature": frame.stack_signature,
            "changed_from_previous": frame.changed_from_previous,
        }
        for frame in result.frames
        if frame.changed_from_previous
    ]

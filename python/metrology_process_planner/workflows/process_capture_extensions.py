"""Shared accessors for process-aware capture extension blocks."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.session import CaptureRecord


def process_extension(capture: CaptureRecord) -> dict[str, object]:
    """Return the first process-aware extension block on a capture."""

    for value in dict(capture.extensions or {}).values():
        if isinstance(value, Mapping) and _looks_process_aware(value):
            return dict(value)
    return {}


def process_solver_request(capture: CaptureRecord) -> dict[str, object]:
    """Return the solver request for a process-aware capture."""

    request = process_extension(capture).get("solver_request", {})
    return dict(request) if isinstance(request, Mapping) else {}


def is_process_aware_capture(capture: CaptureRecord) -> bool:
    """Return whether a capture declares process-output ownership."""

    return bool(process_extension(capture))


def _looks_process_aware(value: Mapping[object, object]) -> bool:
    return (
        isinstance(value.get("solver_request"), Mapping)
        or value.get("process_context_ref") == "process_context.active"
        or "solver_result_id" in value
    )

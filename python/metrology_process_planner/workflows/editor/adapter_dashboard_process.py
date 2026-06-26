"""Process-aware dashboard status helpers."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord, WarningRecord


def process_output_status_counts(session: SessionRecord) -> str:
    """Return compact process output status counts."""

    counts: dict[str, int] = {}
    for output in session.process_outputs:
        counts[output.status] = counts.get(output.status, 0) + 1
    if not counts:
        return "none"
    return ", ".join(f"{status}:{counts[status]}" for status in sorted(counts))


def recipe_status(session: SessionRecord) -> str:
    """Return dashboard status for the active process recipe."""

    codes = _open_process_warning_codes(session)
    if "PROCESS_RECIPE_FINGERPRINT_MISMATCH" in codes:
        return "mismatch"
    if "PROCESS_RECIPE_FILE_NOT_FOUND" in codes:
        return "missing"
    if "PROCESS_RECIPE_PARSE_FAILED" in codes:
        return "parse_failed"
    context = session.process_context
    if not (context.recipe_id or context.recipe_path or context.recipe_name):
        return "none"
    if context.recipe_path and not context.recipe_fingerprint:
        return "attached_unverified"
    return "attached"


def solver_status(session: SessionRecord) -> str:
    """Return dashboard status for process solver availability."""

    if "SOLVER_BACKEND_UNAVAILABLE" in _open_process_warning_codes(session):
        return "unavailable"
    status = str((session.process_context.solver_options or {}).get("status", ""))
    if status:
        return status
    return "configured" if session.process_context.solver_backend else "unavailable"


def open_process_warnings(session: SessionRecord) -> tuple[WarningRecord, ...]:
    """Return open process-context warnings linked to the active context."""

    return tuple(
        warning
        for warning in session.warnings
        if warning.status == "open"
        and warning.source == "process_context"
        and _warning_is_context_linked(session, warning.id)
    )


def _open_process_warning_codes(session: SessionRecord) -> set[str]:
    return {warning.code for warning in open_process_warnings(session)}


def _warning_is_context_linked(session: SessionRecord, warning_id: str) -> bool:
    warning_ids = set(session.process_context.warning_ids)
    return not warning_ids or warning_id in warning_ids

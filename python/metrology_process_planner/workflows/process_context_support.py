"""Support helpers for process-context workflows."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from metrology_process_planner.domains.session import SessionRecord, WarningRecord
from metrology_process_planner.workflows.process_context_models import ProcessContextResult


def recipe_snapshot(recipe: dict[str, Any], policy: str) -> dict[str, Any]:
    """Return the recipe snapshot stored in session JSON."""

    if policy == "reference_only":
        return {}
    if policy == "embed_full_recipe":
        return dict(recipe)
    materials = recipe.get("materials", ())
    steps = recipe.get("steps", recipe.get("process_steps", ()))
    return {
        "materials": [
            {"id": str(item.get("id", "")), "name": str(item.get("name", ""))}
            for item in materials
            if isinstance(item, dict)
        ],
        "step_count": len(steps) if isinstance(steps, list) else 0,
    }


def with_warnings(
    session: SessionRecord,
    warnings: tuple[WarningRecord, ...],
    status: str,
    message: str,
) -> ProcessContextResult:
    """Return a process result with stable warning replacement."""

    incoming = {warning.id: warning for warning in warnings}
    existing = tuple(warning for warning in session.warnings if warning.id not in incoming)
    warning_ids = tuple(dict.fromkeys(session.process_context.warning_ids + tuple(incoming)))
    session = replace(
        session,
        warnings=existing + tuple(incoming.values()),
        process_context=replace(session.process_context, warning_ids=warning_ids),
    )
    return ProcessContextResult(
        session,
        tuple(incoming.values()),
        status,
        message,
        warning_ids=tuple(incoming),
        next_ui_hint="review_warnings" if incoming else "",
    )


def process_warning(
    code: str,
    message: str,
    repair: str,
    item_id: str = "",
) -> WarningRecord:
    """Return a stable process-context warning."""

    related = (f"capture:{item_id}",) if item_id else ("process_context:active",)
    owner_suffix = f"{item_id}-" if item_id else ""
    return WarningRecord(
        f"warn-{owner_suffix}{code.lower()}",
        message,
        severity="warning",
        source="process_context",
        code=code,
        related_item_refs=related,
        repair_suggestion=repair,
    )

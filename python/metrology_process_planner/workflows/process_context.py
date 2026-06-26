"""Recipe attachment and process-context validation workflows."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ProcessContext,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.workflows.process_capture_extensions import is_process_aware_capture
from metrology_process_planner.workflows.process_context_models import (
    AttachRecipeCommand,
    DetachRecipeCommand,
    ProcessContextResult,
    RefreshRecipeFingerprintCommand,
    RegenerateProcessOutputsCommand,
    ValidateProcessContextCommand,
)
from metrology_process_planner.workflows.process_context_result_metadata import (
    updated_process_artifact_ids,
    updated_process_diagnostic_ids,
)
from metrology_process_planner.workflows.process_context_support import (
    process_warning,
    recipe_snapshot,
    with_warnings,
)
from metrology_process_planner.workflows.process_context_validation import (
    process_context_warnings,
)
from metrology_process_planner.workflows.process_output_service import ProcessOutputService
from metrology_process_planner.workflows.process_regeneration import regenerate_capture_outputs


def attach_recipe(session: SessionRecord, command: AttachRecipeCommand) -> ProcessContextResult:
    """Attach a recipe path and persist recipe identity/fingerprint metadata."""

    path = Path(command.recipe_path)
    if not path.exists():
        warning = process_warning(
            "PROCESS_RECIPE_FILE_NOT_FOUND",
            f"Recipe file was not found: {command.recipe_path}",
            "Attach an existing recipe file.",
        )
        return with_warnings(session, (warning,), "warning", "Recipe file not found.")
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        warning = process_warning(
            "PROCESS_RECIPE_PARSE_FAILED",
            f"Recipe could not be parsed: {exc}",
            "Choose a valid recipe JSON file.",
        )
        return with_warnings(session, (warning,), "warning", "Recipe parse failed.")
    recipe = payload if isinstance(payload, dict) else {}
    context = ProcessContext(
        recipe_reference=str(path),
        recipe_id=str(recipe.get("id", recipe.get("recipe_id", path.stem))),
        recipe_name=str(recipe.get("name", recipe.get("recipe_name", path.stem))),
        recipe_version=str(recipe.get("version", "")),
        recipe_path=str(path),
        recipe_fingerprint=hashlib.sha256(raw).hexdigest(),
        recipe_snapshot_policy=command.snapshot_policy,
        recipe_snapshot=recipe_snapshot(recipe, command.snapshot_policy),
        solver_backend="HybridCrossSectionSolver",
        solver_version="0.1.0-alpha",
        solver_options={"status": "available_or_unavailable"},
        render_profile="default_cross_section",
        process_window_variant="target",
    )
    return ProcessContextResult(
        replace(session, process_context=context),
        status="success",
        message="Recipe attached.",
    )


def detach_recipe(session: SessionRecord, command: DetachRecipeCommand) -> ProcessContextResult:
    """Detach the active process recipe from the session."""

    context = ProcessContext(
        solver_backend="HybridCrossSectionSolver",
        solver_options={"status": "unavailable_or_not_configured"},
    )
    return ProcessContextResult(
        replace(session, process_context=context),
        status="success",
        message=command.reason or "Recipe detached.",
    )


def refresh_recipe_fingerprint(
    session: SessionRecord,
    command: RefreshRecipeFingerprintCommand,
) -> ProcessContextResult:
    """Refresh and validate the active recipe fingerprint."""

    path = Path(session.process_context.recipe_path)
    if not path.exists():
        return _recipe_file_warning(session, f"Recipe file was not found: {path}")
    try:
        fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        return _recipe_file_warning(
            session,
            f"Recipe fingerprint could not be refreshed: {exc}",
            "Attach an accessible recipe file.",
            "Recipe fingerprint refresh failed.",
        )
    warning: tuple[WarningRecord, ...] = ()
    if command.expected_fingerprint and command.expected_fingerprint != fingerprint:
        warning = (
            process_warning(
                "PROCESS_RECIPE_FINGERPRINT_MISMATCH",
                "Recipe fingerprint does not match the expected value.",
                "Review the recipe and refresh dependent process outputs.",
            ),
        )
    context = replace(session.process_context, recipe_fingerprint=fingerprint)
    return with_warnings(
        replace(session, process_context=context),
        warning,
        "success",
        "Refreshed.",
    )


def validate_process_context(
    session: SessionRecord,
    command: ValidateProcessContextCommand | None = None,
) -> ProcessContextResult:
    """Validate active process context and return warning records."""

    command = command if command is not None else ValidateProcessContextCommand()
    warnings = process_context_warnings(session, command.require_recipe)
    return with_warnings(
        session,
        tuple(warnings),
        "warning" if warnings else "success",
        "Validated.",
    )


def regenerate_process_outputs(
    session: SessionRecord,
    command: RegenerateProcessOutputsCommand,
) -> ProcessContextResult:
    """Regenerate or update process-output records for process-aware captures."""

    if not command.solver_available:
        warnings: tuple[WarningRecord, ...] = (
            process_warning(
                "SOLVER_BACKEND_UNAVAILABLE",
                "Process output regeneration is waiting for solver configuration.",
                "Configure a solver backend and regenerate process outputs.",
                item_id=command.owner_id,
            ),
        )
        targets = tuple(
            capture
            for capture in session.captures
            if is_process_aware_capture(capture)
            and (not command.owner_id or capture.id == command.owner_id)
        )
        session = ProcessOutputService().ensure_placeholder_outputs(session, targets, warnings)
        return with_warnings(session, warnings, "warning", "Regeneration checked.")
    session, warnings, status, message = regenerate_capture_outputs(session, command)
    return ProcessContextResult(
        session,
        warnings,
        status,
        message,
        updated_capture_id=command.owner_id,
        updated_artifact_ids=updated_process_artifact_ids(session, command.owner_id),
        warning_ids=tuple(warning.id for warning in warnings),
        diagnostic_ids=updated_process_diagnostic_ids(session, command.owner_id),
        next_ui_hint="review_warnings" if warnings else "show_process_output",
    )


def _recipe_file_warning(
    session: SessionRecord,
    message: str,
    repair: str = "Attach an existing recipe file.",
    result_message: str = "Recipe file not found.",
) -> ProcessContextResult:
    """Return a stable recipe-file warning result."""

    return with_warnings(
        session,
        (process_warning("PROCESS_RECIPE_FILE_NOT_FOUND", message, repair),),
        "warning",
        result_message,
    )

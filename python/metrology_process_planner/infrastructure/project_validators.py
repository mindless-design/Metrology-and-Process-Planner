"""Project-wide structured validators for self-audit workflows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from metrology_process_planner.app.command_catalog import ALL_COMMANDS
from metrology_process_planner.domains.modes.mode_registry import (
    ModeRegistry,
    built_in_mode_registry,
)
from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.domains.warnings.warning_visibility import session_is_process_aware
from metrology_process_planner.infrastructure.validation_models import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    issue,
)
from metrology_process_planner.persistence.schema import validate_session_payload
from metrology_process_planner.rendering import built_in_render_profiles


def validate_session_json(data: Mapping[str, Any]) -> ValidationReport:
    """Validate raw session JSON without raising on recoverable problems."""

    issues = tuple(
        issue(
            ValidationSeverity.WARNING,
            "session_json",
            "session",
            message,
            "Save or repair the session in the current schema.",
        )
        for message in validate_session_payload(data)
    )
    return ValidationReport("session_json", issues)


def validate_session_record(session: SessionRecord) -> ValidationReport:
    """Validate canonical session object relationships and references."""

    issues: list[ValidationIssue] = []
    issues.extend(_duplicate_ids("captures", (capture.id for capture in session.captures)))
    issues.extend(_duplicate_ids("pending_captures", (i.id for i in session.pending_captures)))
    issues.extend(_duplicate_ids("canvas_objects", (item.id for item in session.canvas_objects)))
    issues.extend(_capture_reference_issues(session))
    issues.extend(_artifact_reference_issues(session))
    issues.extend(_process_context_issues(session))
    return ValidationReport(f"session:{session.id}", tuple(issues))


def validate_modes(registry: ModeRegistry | None = None) -> ValidationReport:
    """Validate mode definitions and registry metadata."""

    registry = registry or built_in_mode_registry()
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for definition in registry.definitions():
        location = f"modes.{definition.mode_id or '<missing>'}"
        if not definition.mode_id:
            issues.append(_error("mode_definitions", location, "Mode id is missing."))
        if definition.mode_id in seen:
            issues.append(_error("mode_definitions", location, "Duplicate mode id."))
        seen.add(definition.mode_id)
        for message in definition.validation_warnings():
            issues.append(_warning("mode_definitions", location, message))
    return ValidationReport("mode_definitions", tuple(issues))


def validate_commands() -> ValidationReport:
    """Validate command registration metadata."""

    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for spec in ALL_COMMANDS:
        location = f"commands.{spec.command_id.value}"
        if spec.command_id.value in seen:
            issues.append(_error("command_registration", location, "Duplicate command id."))
        seen.add(spec.command_id.value)
        if not spec.title:
            issues.append(_error("command_registration", location, "Command title is missing."))
        if spec.appears_in_menu and not spec.menu_path.startswith("tools_menu."):
            issues.append(_warning("command_registration", location, "Menu path is unstable."))
    return ValidationReport("command_registration", tuple(issues))


def validate_render_profiles() -> ValidationReport:
    """Validate built-in render profiles used by modes and process outputs."""

    issues: list[ValidationIssue] = []
    profiles = built_in_render_profiles()
    for profile_id, profile in profiles.items():
        location = f"render_profiles.{profile_id}"
        if profile.output_size[0] <= 0 or profile.output_size[1] <= 0:
            issues.append(_error("render_profiles", location, "Output size must be positive."))
        if not profile.export_formats:
            issues.append(_warning("render_profiles", location, "No export formats declared."))
    return ValidationReport("render_profiles", tuple(issues))


def validate_recipe_definition(recipe: ProcessRecipe) -> ValidationReport:
    """Validate a process recipe as structured diagnostics."""

    issues = tuple(
        _warning("recipe_definitions", f"recipes.{recipe.id}", message)
        for message in recipe.validate()
    )
    return ValidationReport(f"recipe:{recipe.id}", issues)


def validate_fixture_sessions(paths: Sequence[Path]) -> ValidationReport:
    """Validate session fixture JSON files using the raw schema validator."""

    import json

    reports: list[ValidationIssue] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, Mapping):
            reports.extend(
                issue(
                    item.severity,
                    item.category,
                    f"{path.name}:{item.location}",
                    item.message,
                    item.repair_suggestion,
                )
                for item in validate_session_json(data).issues
            )
    return ValidationReport("fixture_sessions", tuple(reports))


def _capture_reference_issues(session: SessionRecord) -> list[ValidationIssue]:
    capture_ids = {capture.id for capture in session.captures}
    issues: list[ValidationIssue] = []
    for pending in session.pending_captures:
        if pending.parent_id and pending.parent_id not in capture_ids:
            issues.append(
                _warning("capture_definitions", f"pending.{pending.id}", "Orphaned capture.")
            )
    for item in session.canvas_objects:
        if item.record_id and item.record_id not in capture_ids:
            issues.append(
                _warning("capture_definitions", f"canvas.{item.id}", "Broken record link.")
            )
    return issues


def _artifact_reference_issues(session: SessionRecord) -> list[ValidationIssue]:
    artifact_ids = set((session.artifacts or {}).keys())
    issues: list[ValidationIssue] = []
    for owner, refs in _artifact_ref_mappings(session):
        for role, artifact_id in refs.items():
            if artifact_id not in artifact_ids:
                issues.append(
                    _warning("artifact_registry", f"{owner}.{role}", "Broken artifact reference.")
                )
    return issues


def _artifact_ref_mappings(session: SessionRecord) -> tuple[tuple[str, Mapping[str, str]], ...]:
    rows: list[tuple[str, Mapping[str, str]]] = []
    rows.extend((f"captures.{item.id}", item.artifact_refs or {}) for item in session.captures)
    rows.extend((f"setup.{item.id}", item.artifact_refs or {}) for item in session.setup.items)
    if session_is_process_aware(session):
        rows.extend((f"outputs.{o.id}", o.artifact_refs or {}) for o in session.process_outputs)
    rows.extend((f"reports.{item.id}", item.artifact_refs or {}) for item in session.reports)
    return tuple(rows)


def _process_context_issues(session: SessionRecord) -> list[ValidationIssue]:
    if not session_is_process_aware(session):
        return []
    if not session.process_context.render_profile:
        return []
    if session.process_context.render_profile in built_in_render_profiles():
        return []
    return [
        _warning(
            "workflow_definitions",
            "process_context.render_profile",
            "Unknown render profile.",
        )
    ]


def _duplicate_ids(category: str, ids: Iterable[str]) -> list[ValidationIssue]:
    seen: set[str] = set()
    issues: list[ValidationIssue] = []
    for item_id in ids:
        if not item_id:
            issues.append(_error(category, category, "Record id is missing."))
        if item_id in seen:
            issues.append(_error(category, f"{category}.{item_id}", "Duplicate record id."))
        seen.add(item_id)
    return issues


def _error(category: str, location: str, message: str) -> ValidationIssue:
    return issue(
        ValidationSeverity.ERROR,
        category,
        location,
        message,
        "Repair the record id or metadata.",
    )


def _warning(category: str, location: str, message: str) -> ValidationIssue:
    return issue(
        ValidationSeverity.WARNING,
        category,
        location,
        message,
        "Review and regenerate this record.",
    )

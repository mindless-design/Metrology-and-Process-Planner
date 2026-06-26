"""Typed process-context workflow commands and results."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.session import SessionRecord, WarningRecord


@dataclass(frozen=True)
class AttachRecipeCommand:
    """Attach a process recipe to the active session."""

    recipe_path: str
    snapshot_policy: str = "embed_minimal_summary"


@dataclass(frozen=True)
class DetachRecipeCommand:
    """Detach the active process recipe."""

    reason: str = ""


@dataclass(frozen=True)
class RefreshRecipeFingerprintCommand:
    """Refresh the active recipe fingerprint."""

    expected_fingerprint: str = ""


@dataclass(frozen=True)
class ValidateProcessContextCommand:
    """Validate process context and return structured warnings."""

    require_recipe: bool = True


@dataclass(frozen=True)
class RegenerateProcessOutputsCommand:
    """Request process-output regeneration for a capture or session."""

    owner_id: str = ""
    solver_available: bool = True
    explicit: bool = True


@dataclass(frozen=True)
class ProcessContextResult:
    """Result of a process-context workflow action."""

    session: SessionRecord
    warnings: tuple[WarningRecord, ...] = ()
    status: str = "success"
    message: str = ""
    updated_capture_id: str = ""
    updated_artifact_ids: tuple[str, ...] = ()
    warning_ids: tuple[str, ...] = ()
    diagnostic_ids: tuple[str, ...] = ()
    next_ui_hint: str = ""

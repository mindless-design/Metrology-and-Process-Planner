"""Graceful fallback helpers for unsupported saved session modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from metrology_process_planner.domains.session.warnings import WarningRecord
from metrology_process_planner.domains.session.workflow import AuditEvent


@dataclass(frozen=True)
class ModeFallbackResult:
    """Resolved mode plus warning, audit, and extension updates."""

    mode: Any
    warnings: tuple[WarningRecord, ...]
    audit: tuple[AuditEvent, ...]
    extensions: Mapping[str, Any]
    unsupported: bool = False


def apply_mode_fallback(
    mode_type: Any,
    requested: str,
    warnings: tuple[WarningRecord, ...] = (),
    audit: tuple[AuditEvent, ...] = (),
    extensions: Optional[Mapping[str, Any]] = None,
) -> ModeFallbackResult:
    """Return a supported mode, preserving unsupported mode details when needed."""

    try:
        return ModeFallbackResult(
            mode_type(requested),
            warnings,
            audit,
            dict(extensions or {}),
        )
    except ValueError:
        fallback = mode_type("simple_capture")
        warning = _mode_warning(requested, fallback.value)
        event = _mode_audit(requested, fallback.value)
        return ModeFallbackResult(
            fallback,
            _upsert_warning(warnings, warning),
            _upsert_audit(audit, event),
            _mode_extensions(extensions or {}, requested, fallback.value),
            unsupported=True,
        )


def _mode_warning(requested: str, fallback: str) -> WarningRecord:
    return WarningRecord(
        id="mode-validation-unsupported",
        severity="warning",
        source="mode_validation",
        code="unsupported_mode",
        related_item_refs=("session",),
        message=f"Unsupported session mode '{requested}' loaded as '{fallback}'.",
        technical_details=(
            "The saved session references a mode that is not registered in this build."
        ),
        repair_suggestion="Install/register the missing mode or save as a supported mode.",
    )


def _mode_audit(requested: str, fallback: str) -> AuditEvent:
    return AuditEvent(
        id=f"audit-mode-fallback-{requested}",
        event_type="mode_fallback",
        message=f"Session mode '{requested}' loaded as '{fallback}'.",
        source="mode_validation",
        details={"requested_mode": requested, "fallback_mode": fallback},
    )


def _mode_extensions(
    extensions: Mapping[str, Any],
    requested: str,
    fallback: str,
) -> dict[str, Any]:
    updated = dict(extensions)
    updated["mode_validation"] = {
        "requested_mode": requested,
        "fallback_mode": fallback,
        "status": "unsupported",
    }
    return updated


def _upsert_warning(
    warnings: tuple[WarningRecord, ...],
    warning: WarningRecord,
) -> tuple[WarningRecord, ...]:
    return tuple(item for item in warnings if item.id != warning.id) + (warning,)


def _upsert_audit(
    audit: tuple[AuditEvent, ...],
    event: AuditEvent,
) -> tuple[AuditEvent, ...]:
    return tuple(item for item in audit if item.id != event.id) + (event,)

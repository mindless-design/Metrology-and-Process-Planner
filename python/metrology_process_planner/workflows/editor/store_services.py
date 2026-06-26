"""Migration and validation services for editor document stores."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.schema import validate_session_payload
from metrology_process_planner.workflows.editor.store_io import allowed_modes


class SessionMigrationService:
    """Convert legacy or partial session payloads into the current session model."""

    def __init__(self, mode_registry: ModeRegistry | None = None) -> None:
        self._mode_registry = mode_registry

    def migrate(self, payload: Mapping[str, Any]) -> SessionRecord:
        """Return a current SessionRecord, preserving migration audit when available."""
        return SessionRecord.from_dict(payload, allowed_modes(self._mode_registry))


class SessionValidationService:
    """Validate session document payloads for open and save operations."""

    def validate_payload(self, payload: Mapping[str, Any]) -> tuple[str, ...]:
        """Return non-blocking validation warnings for a loaded payload."""
        return validate_session_payload(payload)

    def validate_for_save(self, payload: Mapping[str, Any]) -> None:
        """Raise if a payload is not safe to write as session JSON."""
        warnings = validate_session_payload(payload)
        blocking = [message for message in warnings if "Unsupported schema" in message]
        if blocking:
            raise ValueError("; ".join(blocking))

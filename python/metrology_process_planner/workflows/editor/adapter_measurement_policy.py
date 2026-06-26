"""Mode-aware measurement action policy."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)


def mode_supports_measurements(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> bool:
    """Return whether the active mode allows capture-owned measurements."""

    definition = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    return bool(definition.capabilities.supports_measurements or definition.measurements.enabled)

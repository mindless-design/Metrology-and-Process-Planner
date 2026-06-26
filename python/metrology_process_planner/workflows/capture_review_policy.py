"""Mode-aware capture review policy helpers."""

from __future__ import annotations

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord


def mode_requires_capture_review(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> bool:
    """Return whether normal box captures should pause in pending review."""

    from metrology_process_planner.domains.session import built_in_mode_registry

    registry = mode_registry or built_in_mode_registry()
    return registry.definition(session.mode.value).capture.review

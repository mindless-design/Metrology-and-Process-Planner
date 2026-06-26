"""Mode setup readiness guards for normal capture commits."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.workflows.setup_guide_requirements import (
    incomplete_required_setup_labels,
)


def capture_blocking_setup_labels(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[str, ...]:
    """Return required setup labels that must be completed before normal capture."""

    mode = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    if not mode.setup.stage_types:
        return ()
    return incomplete_required_setup_labels(session, mode)


def capture_blocked_by_setup_message(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> str:
    """Return a concise user-facing setup block message."""

    labels = capture_blocking_setup_labels(session, mode_registry)
    if not labels:
        return ""
    return "Complete required setup before capture: " + ", ".join(labels) + "."

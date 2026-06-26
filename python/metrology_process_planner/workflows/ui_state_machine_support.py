"""Support helpers for modeless UI state-machine evaluators."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord


def pending_measurement_ref(session: SessionRecord) -> str:
    """Return the first pending measurement item reference, if any."""

    for capture in session.captures:
        for measurement in capture.measurements:
            if dict(measurement.metadata or {}).get("workflow_state") == "pending":
                return f"measurement:{measurement.id}"
    return ""

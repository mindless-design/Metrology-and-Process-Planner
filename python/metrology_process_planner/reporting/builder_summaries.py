"""Capture and measurement summary builders for report documents."""

from __future__ import annotations

from metrology_process_planner.domains.session import CaptureRecord, ModeRegistry, SessionRecord
from metrology_process_planner.reporting.models import CaptureSummary, MeasurementSummary
from metrology_process_planner.reporting.visibility import visible_artifact_refs
from metrology_process_planner.workflows.editor.document import SessionDocument


def capture_summary(
    session: SessionRecord,
    capture: CaptureRecord,
    mode_registry: ModeRegistry,
) -> CaptureSummary:
    """Return a report capture summary for one capture."""

    return CaptureSummary(
        capture.id,
        capture.label,
        capture.role,
        capture.status,
        capture.geometry.kind.value,
        len(capture.measurements),
        visible_artifact_refs(
            session,
            tuple((capture.artifact_refs or {}).values()),
            mode_registry,
        ),
        capture.notes,
    )


def measurement_summaries(
    document: SessionDocument,
    mode_registry: ModeRegistry,
) -> tuple[MeasurementSummary, ...]:
    """Return report measurement summaries for all session captures."""

    summaries: list[MeasurementSummary] = []
    for capture in document.session.captures:
        for measurement in capture.measurements:
            summaries.append(
                MeasurementSummary(
                    measurement.id,
                    capture.id,
                    measurement.label,
                    measurement.measured_length,
                    measurement.target,
                    measurement.lower_spec_limit,
                    measurement.upper_spec_limit,
                    visible_artifact_refs(
                        document.session,
                        tuple((measurement.artifact_refs or {}).values()),
                        mode_registry,
                    ),
                )
            )
    return tuple(summaries)

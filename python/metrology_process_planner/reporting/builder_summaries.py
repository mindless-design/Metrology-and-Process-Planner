"""Capture and measurement summary builders for report documents."""

from __future__ import annotations

from metrology_process_planner.domains.session import CaptureRecord, ModeRegistry, SessionRecord
from metrology_process_planner.domains.session.display_units import (
    DisplayUnitPreferences,
    display_unit_preferences_from_session,
    format_length,
    resolved_display_unit,
)
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
    preferences = display_unit_preferences_from_session(document.session)
    canonical_unit = document.session.coordinates.units
    for capture in document.session.captures:
        for measurement in capture.measurements:
            display_unit = _measurement_display_unit(
                measurement.measured_length,
                canonical_unit,
                preferences,
            )
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
                    display_unit,
                    format_length(measurement.measured_length, canonical_unit, display_unit),
                    format_length(measurement.target, canonical_unit, display_unit),
                    format_length(measurement.lower_spec_limit, canonical_unit, display_unit),
                    format_length(measurement.upper_spec_limit, canonical_unit, display_unit),
                )
            )
    return tuple(summaries)


def _measurement_display_unit(
    measured_length: float,
    canonical_unit: str,
    preferences: DisplayUnitPreferences,
) -> str:
    preference = preferences.reports
    if preference == "auto":
        preference = preferences.layout_geometry
    return resolved_display_unit(measured_length, canonical_unit, preference)

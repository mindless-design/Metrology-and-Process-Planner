"""Helpers for promoting pending measurement records."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.measurement.records import MeasurementRecord


def saved_measurements(
    measurements: tuple[MeasurementRecord, ...],
) -> tuple[tuple[MeasurementRecord, ...], int]:
    """Return measurements with pending records promoted and counted."""

    saved = []
    saved_count = 0
    for measurement in measurements:
        metadata = dict(measurement.metadata or {})
        if metadata.get("workflow_state") == "pending":
            metadata["workflow_state"] = "saved"
            metadata["completion_prompt_pending"] = True
            saved_count += 1
            saved.append(replace(measurement, metadata=metadata))
        else:
            metadata.pop("completion_prompt_pending", None)
            saved.append(replace(measurement, metadata=metadata))
    return tuple(saved), saved_count

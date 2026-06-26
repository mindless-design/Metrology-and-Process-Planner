"""CSV backend for machine-readable report summaries."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from metrology_process_planner.reporting.models import ReportDocument, TableModel
from metrology_process_planner.reporting.tables import (
    artifact_table,
    capture_table,
    measurement_table,
)


class CsvReportBackend:
    """Export report summary tables to CSV files."""

    format_name = "csv"

    def export(self, document: ReportDocument, destination: Path) -> Path:
        """Write a primary CSV summary and related inventory CSV files."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        _write_table(capture_table(document.captures), destination)
        stem = destination.with_suffix("")
        measurements_path = stem.with_name(stem.name + ".measurements.csv")
        artifacts_path = stem.with_name(stem.name + ".artifacts.csv")
        _write_table(measurement_table(document.measurements), measurements_path)
        _write_table(artifact_table(document.artifacts), artifacts_path)
        return destination


def _write_table(table: TableModel, destination: Path) -> None:
    fields = [column[0] for column in table.columns]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in table.rows:
            writer.writerow(_row_values(fields, row))


def _row_values(fields: list[str], row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in fields}

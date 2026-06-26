"""Integrated project diagnostics bundle models."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from metrology_process_planner.diagnostics.diagnostics_models import DiagnosticsSnapshot
from metrology_process_planner.infrastructure.timing import TimingMetric
from metrology_process_planner.infrastructure.validation_models import (
    HealthCheckReport,
    ValidationReport,
)


@dataclass(frozen=True)
class ProjectDiagnosticsBundle:
    """Portable diagnostics bundle for developer support and review."""

    snapshot: DiagnosticsSnapshot
    health: HealthCheckReport
    validation_reports: tuple[ValidationReport, ...]
    timings: tuple[TimingMetric, ...] = ()
    memory_usage_estimate_bytes: int = 0

    def to_dict(self) -> dict[str, object]:
        """Serialize the bundle to JSON-compatible structured data."""

        return {
            "snapshot": self.snapshot.to_dict(),
            "health": self.health.to_dict(),
            "validation_reports": [report.to_dict() for report in self.validation_reports],
            "timings": [metric.to_dict() for metric in self.timings],
            "memory_usage_estimate_bytes": self.memory_usage_estimate_bytes,
        }

    def export(self, path: Path) -> Path:
        """Write the diagnostics bundle to a JSON file."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path


def estimate_memory_usage(value: object) -> int:
    """Return a practical recursive memory usage estimate for diagnostics."""

    seen: set[int] = set()
    return _estimate(value, seen)


def _estimate(value: object, seen: set[int]) -> int:
    value_id = id(value)
    if value_id in seen:
        return 0
    seen.add(value_id)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        return size + sum(_estimate(k, seen) + _estimate(v, seen) for k, v in value.items())
    if isinstance(value, (list, tuple, set, frozenset)):
        return size + sum(_estimate(item, seen) for item in value)
    if hasattr(value, "__dict__"):
        return size + _estimate(vars(value), seen)
    return size

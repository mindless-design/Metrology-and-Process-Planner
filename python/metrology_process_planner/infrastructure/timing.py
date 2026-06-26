"""Timing instrumentation primitives for diagnostics and health checks."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter


@dataclass(frozen=True)
class TimingMetric:
    """Elapsed timing measurement for one named operation."""

    operation: str
    elapsed_ms: float
    category: str = "performance"

    def to_dict(self) -> dict[str, object]:
        """Serialize the metric to JSON-compatible data."""

        return {
            "operation": self.operation,
            "elapsed_ms": round(self.elapsed_ms, 3),
            "category": self.category,
        }


class TimingCollector:
    """Collect elapsed timings around expensive project operations."""

    def __init__(self) -> None:
        self._metrics: list[TimingMetric] = []

    @contextmanager
    def measure(self, operation: str, category: str = "performance") -> Iterator[None]:
        """Measure elapsed time for a block and record it as a metric."""

        start = perf_counter()
        try:
            yield
        finally:
            elapsed = (perf_counter() - start) * 1000
            self._metrics.append(TimingMetric(operation, elapsed, category))

    def metrics(self) -> tuple[TimingMetric, ...]:
        """Return collected metrics in insertion order."""

        return tuple(self._metrics)

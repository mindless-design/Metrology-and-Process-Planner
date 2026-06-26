"""Structured dashboard models for diagnostics shells."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.ui.shell.view_models import EditorActionViewModel


@dataclass(frozen=True)
class DiagnosticsDashboardRow:
    """One scannable diagnostics dashboard row."""

    label: str
    value: str
    status: str = "available"


@dataclass(frozen=True)
class DiagnosticsDashboardSection:
    """A diagnostics dashboard section with related rows."""

    section_id: str
    title: str
    rows: tuple[DiagnosticsDashboardRow, ...]


@dataclass(frozen=True)
class DiagnosticsDashboardModel:
    """Production-facing diagnostics dashboard model."""

    sections: tuple[DiagnosticsDashboardSection, ...]
    actions: tuple[EditorActionViewModel, ...]


def diagnostics_dashboard(result: Any) -> DiagnosticsDashboardModel:
    """Build a structured dashboard from diagnostics controller output."""

    rows = dict(getattr(result, "summary_rows", ()))
    actions = tuple(getattr(result, "actions", ()))
    return DiagnosticsDashboardModel(
        tuple(
            _section(section_id, title, labels, rows)
            for section_id, title, labels in _sections_for_rows(rows)
        ),
        actions,
    )


def _section(
    section_id: str,
    title: str,
    labels: tuple[str, ...],
    rows: dict[str, str],
) -> DiagnosticsDashboardSection:
    return DiagnosticsDashboardSection(
        section_id,
        title,
        tuple(DiagnosticsDashboardRow(label, rows.get(label, "unavailable"))
              for label in labels),
    )


def _sections_for_rows(rows: dict[str, str]) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    if rows.get("Mode Process Aware") == "true":
        return _PROCESS_AWARE_SECTIONS
    return _RECIPE_FREE_SECTIONS


_COMMON_SECTIONS = (
    (
        "session",
        "Session",
        (
            "Session",
            "Active Session ID",
            "Session Path",
            "Active Session Path",
            "Dirty State",
            "Mode",
            "Display Units",
            "Active Mode",
            "Loaded Modes",
            "Mode Validation",
        ),
    ),
    (
        "workflow",
        "Workflow",
        (
            "Workflow State",
            "Armed Capture Tool",
            "Selected Editor Item",
            "Selected Canvas Object",
        ),
    ),
    (
        "mode_policy",
        "Mode Policy",
        (
            "Loaded Mode Definition",
            "Mode Process Aware",
            "Recipe Required",
            "Solver Operation",
            "Process Context Visible",
            "Setup State",
            "Capture State",
            "Measurement Workflow",
        ),
    ),
    (
        "artifacts",
        "Artifacts",
        ("Artifacts", "Artifact Repair Queue", "Warnings", "Missing Artifacts"),
    ),
)


_PROCESS_AWARE_SECTIONS = _COMMON_SECTIONS + (
    (
        "process_report",
        "Process And Reports",
        ("Recipe Context", "Solver Backend", "Renderer Backend", "Report Readiness"),
    ),
    ("activity", "Activity", ("Recent Commands", "Recent Failures", "Open Windows")),
)


_RECIPE_FREE_SECTIONS = _COMMON_SECTIONS + (
    ("reports", "Reports", ("Report Readiness",)),
    ("activity", "Activity", ("Recent Commands", "Recent Failures", "Open Windows")),
)

"""Report output destination selection contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from metrology_process_planner.app.session_path_adapter import PathSelection


class ReportOutputAdapter(Protocol):
    """Boundary implemented by UI shells for report output folders."""

    def select_report_output_dir(self, current_dir: Path) -> PathSelection:
        """Return a report output folder selected by the operator."""


class UnavailableReportOutputAdapter:
    """Default adapter when no output-folder picker is connected."""

    def select_report_output_dir(self, current_dir: Path) -> PathSelection:
        """Report that destination selection is not connected."""

        return PathSelection(
            status="unavailable",
            message=f"Report output selection requires a folder picker: {current_dir}",
        )

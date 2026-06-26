"""KLayout picker adapter for report output folders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from metrology_process_planner.app.report_output_adapter import ReportOutputAdapter
from metrology_process_planner.app.session_path_adapter import PathSelection


class KLayoutReportOutputAdapter(ReportOutputAdapter):
    """Collect report output folders from KLayout/Qt dialogs."""

    def __init__(self, pya_module: Any) -> None:
        self._pya = pya_module

    def select_report_output_dir(self, current_dir: Path) -> PathSelection:
        """Ask for a report output folder."""

        dialog = getattr(self._pya, "QFileDialog", None)
        if dialog is None or not hasattr(dialog, "getExistingDirectory"):
            return PathSelection(status="unavailable", message="KLayout folder picker unavailable.")
        folder = str(
            dialog.getExistingDirectory(
                None,
                "Choose Report Output Folder",
                str(current_dir),
            )
        )
        if not folder:
            return PathSelection(message="Report output selection cancelled.")
        return PathSelection.selected(folder)

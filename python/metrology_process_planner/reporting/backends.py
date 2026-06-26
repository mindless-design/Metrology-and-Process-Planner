"""Backend orchestration for report exports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from metrology_process_planner.reporting.manifest import ReportManifestBuilder
from metrology_process_planner.reporting.models import ReportDocument


class ReportBackend(Protocol):
    """Protocol for one output backend."""

    format_name: str

    def export(self, document: ReportDocument, destination: Path) -> Path:
        """Export a report document and return the output path."""


@dataclass(frozen=True)
class ExportedReport:
    """Paths produced by a report export run."""

    outputs: dict[str, Path]
    manifest_path: Path


class ReportExporter:
    """Export a report document through one or more backends."""

    def __init__(
        self,
        backends: tuple[ReportBackend, ...],
        manifest_builder: ReportManifestBuilder | None = None,
    ) -> None:
        self._backends = backends
        self._manifest_builder = manifest_builder or ReportManifestBuilder()

    def export(self, document: ReportDocument, output_folder: Path) -> ExportedReport:
        """Export all configured formats and a manifest."""

        output_folder.mkdir(parents=True, exist_ok=True)
        outputs: dict[str, Path] = {}
        for backend in self._backends:
            path = output_folder / f"{document.metadata.report_id}.{backend.format_name}"
            outputs[backend.format_name] = backend.export(document, path)
        manifest = self._manifest_builder.write(
            document,
            tuple(outputs.keys()),
            output_folder / f"{document.metadata.report_id}.manifest.json",
            {format_name: str(path) for format_name, path in outputs.items()},
        )
        return ExportedReport(outputs, manifest)

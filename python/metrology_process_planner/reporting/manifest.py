"""Report output manifest generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from metrology_process_planner.reporting.models import ReportDocument


class ReportManifestBuilder:
    """Build machine-readable manifests for generated reports."""

    def build(
        self,
        document: ReportDocument,
        export_formats: tuple[str, ...],
        output_files: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Return a JSON-compatible report manifest."""

        metadata = document.metadata
        return {
            "report_id": metadata.report_id,
            "report_version": "1",
            "generator_version": metadata.generator_version,
            "timestamp": metadata.generated_at,
            "source_session": {
                "id": metadata.source_session_id,
                "name": metadata.source_session_name,
            },
            "artifact_list": [artifact.artifact_id for artifact in document.artifacts],
            "included_sections": [section.section_id for section in document.sections],
            "theme": metadata.theme_id,
            "layout_metadata": _layout_metadata(document),
            "missing_placeholder_artifacts": _placeholder_artifacts(document),
            "warnings": [warning.message for warning in document.warnings],
            "report_template": metadata.template_id,
            "export_formats": list(export_formats),
            "output_files": dict(output_files or {}),
        }

    def write(
        self,
        document: ReportDocument,
        export_formats: tuple[str, ...],
        destination: Path,
        output_files: dict[str, str] | None = None,
    ) -> Path:
        """Write a manifest JSON file and return its path."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = self.build(document, export_formats, output_files)
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return destination


def _placeholder_artifacts(document: ReportDocument) -> list[str]:
    return [artifact.artifact_id for artifact in document.artifacts if artifact.placeholder]


def _layout_metadata(document: ReportDocument) -> dict[str, Any]:
    return {
        "page_or_slide_size": "screen4x3",
        "sections": [
            {
                "section_id": section.section_id,
                "tables": len(section.tables),
                "figures": len(section.figures),
                "placeholders": sum(1 for figure in section.figures if figure.placeholder),
            }
            for section in document.sections
        ],
    }

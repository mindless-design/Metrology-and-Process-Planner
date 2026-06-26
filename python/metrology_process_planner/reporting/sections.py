"""Reusable report section generators."""

from __future__ import annotations

from collections.abc import Callable

import metrology_process_planner.reporting.tables as tables
from metrology_process_planner.reporting.gallery import gallery_figures
from metrology_process_planner.reporting.models import ReportDocument, ReportSection
from metrology_process_planner.reporting.overview import OVERVIEW_SECTIONS, overview_section


class SectionGenerator:
    """Generate one section by identifier."""

    def __init__(
        self,
        custom: dict[str, Callable[[ReportDocument], ReportSection]] | None = None,
    ) -> None:
        self._custom = dict(custom or {})

    def generate(self, section_id: str, document: ReportDocument) -> ReportSection:
        """Return a report section for the requested section id."""

        section_id = _canonical_section_id(section_id)
        if section_id in self._custom:
            return self._custom[section_id](document)
        if section_id in _STANDARD_SECTIONS:
            return _STANDARD_SECTIONS[section_id](document)
        if section_id in OVERVIEW_SECTIONS:
            return overview_section(section_id, document.artifacts)
        if section_id in {"artifact_gallery", "cross_section_gallery", "process_flow_gallery"}:
            return _gallery(section_id, document)
        if section_id == "process_context":
            return _process_context(document)
        if section_id == "appendix":
            return _appendix(document)
        return ReportSection(section_id, section_id.replace("_", " ").title())


def _canonical_section_id(section_id: str) -> str:
    aliases = {
        "cover": "cover_page",
        "session_summary": "session_summary",
        "setup_references": "setup_summary",
        "capture_gallery": "artifact_gallery",
        "site_captures": "artifact_gallery",
        "overview_maps": "artifact_gallery",
        "session_overview": "session_overview",
        "metrology_overview": "metrology_overview",
        "grid_overview": "grid_overview",
        "cad_review_overview": "cad_review_overview",
        "process_planning_overview": "process_planning_overview",
        "process_flow_frames": "process_flow_gallery",
        "measurement_summary": "measurement_table",
        "measurement_details": "measurement_table",
        "warnings": "warning_summary",
        "process_outputs": "process_context",
        "process_context": "process_context",
    }
    return aliases.get(section_id, section_id)


def _revision_history(_document: ReportDocument) -> ReportSection:
    return ReportSection("revision_history", "Revision History", ("Initial generated report.",))


def _cover_page(document: ReportDocument) -> ReportSection:
    metadata = document.metadata
    return ReportSection(
        "cover_page",
        metadata.title,
        (
            f"Template: {metadata.template_name}",
            f"Source session: {metadata.source_session_name} ({metadata.source_session_id})",
            f"Generated: {metadata.generated_at}",
        ),
    )


def _session_summary(document: ReportDocument) -> ReportSection:
    body = tuple(f"{key}: {value}" for key, value in sorted(document.session_summary.items()))
    return ReportSection("session_summary", "Session Summary", body)


def _setup_summary(document: ReportDocument) -> ReportSection:
    setup = document.appendix_data.get("setup", {})
    table = tables.setup_status_table(setup if isinstance(setup, dict) else {})
    return ReportSection("setup_summary", "Setup Summary", tables=(table,))


def _capture_table(document: ReportDocument) -> ReportSection:
    return ReportSection(
        "capture_table",
        "Captures",
        tables=(tables.capture_table(document.captures),),
    )


def _measurement_table(document: ReportDocument) -> ReportSection:
    return ReportSection(
        "measurement_table",
        "Measurements",
        tables=(tables.measurement_table(document.measurements),),
    )


def _warning_summary(document: ReportDocument) -> ReportSection:
    return ReportSection(
        "warning_summary",
        "Warnings",
        tables=(tables.warning_table(document.warnings),),
    )


def _grid_dataset(document: ReportDocument) -> ReportSection:
    rows = document.appendix_data.get("grid_datasets", ())
    grid_rows = rows if isinstance(rows, tuple) else ()
    return ReportSection(
        "grid_dataset",
        "Grid Datasets",
        tables=(tables.grid_dataset_table(grid_rows),),
    )


def _gallery(section_id: str, document: ReportDocument) -> ReportSection:
    figures = gallery_figures(document.artifacts)
    return ReportSection(section_id, section_id.replace("_", " ").title(), figures=figures)


def _process_context(document: ReportDocument) -> ReportSection:
    body = tuple(
        f"{key}: {value}"
        for key, value in sorted(document.process_context_summary.items())
        if value
    )
    if not body:
        body = ("No process context is attached to this session.",)
    return ReportSection("process_context", "Process Context", body)


def _appendix(document: ReportDocument) -> ReportSection:
    return ReportSection(
        "appendix",
        "Appendix",
        tables=(tables.artifact_table(document.artifacts),),
        appendix=True,
    )


_STANDARD_SECTIONS: dict[str, Callable[[ReportDocument], ReportSection]] = {
    "cover_page": _cover_page,
    "revision_history": _revision_history,
    "session_summary": _session_summary,
    "setup_summary": _setup_summary,
    "capture_table": _capture_table,
    "measurement_table": _measurement_table,
    "warning_summary": _warning_summary,
    "grid_dataset": _grid_dataset,
}

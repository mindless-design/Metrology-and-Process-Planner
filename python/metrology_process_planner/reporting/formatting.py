"""Derived report text used by visual exporters."""

from __future__ import annotations

from metrology_process_planner.reporting.models import (
    FigureModel,
    ReportDocument,
    ReportSection,
    TableModel,
)


def document_footer(document: ReportDocument, page_number: int, page_count: int) -> str:
    """Return compact provenance text for report footers."""

    metadata = document.metadata
    return (
        f"{metadata.source_session_name} | {metadata.template_name} | "
        f"{metadata.generated_at} | {page_number}/{page_count}"
    )


def section_context(document: ReportDocument, section: ReportSection) -> str:
    """Return compact source context for a report section."""

    return (
        f"Session {document.metadata.source_session_id} | "
        f"Section {section.section_id} | Theme {document.metadata.theme_id}"
    )


def figure_caption(figure: FigureModel) -> str:
    """Return a renderer-neutral figure caption."""

    status = "placeholder" if figure.placeholder else "present"
    detail = figure.notes if figure.placeholder and figure.notes else f"Path: {figure.path}"
    return (
        f"Figure {figure.number}: {figure.title} | Artifact {figure.artifact_id} | "
        f"Status: {status} | {detail}"
    )


def table_caption(table: TableModel) -> str:
    """Return a renderer-neutral table caption."""

    row_label = "row" if len(table.rows) == 1 else "rows"
    return f"Table {table.number}: {table.title} | {len(table.rows)} {row_label}"


def toc_lines(document: ReportDocument) -> tuple[str, ...]:
    """Return numbered table-of-contents lines."""

    return tuple(
        f"{index}. {section.title}"
        for index, section in enumerate(document.sections, start=1)
    )


def concise(value: object, limit: int = 64) -> str:
    """Return a compact display string without mutating machine-readable exports."""

    text = str(value)
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."

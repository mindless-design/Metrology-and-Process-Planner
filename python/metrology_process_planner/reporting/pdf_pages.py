"""Printable PDF page text composition."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.reporting.formatting import (
    concise,
    document_footer,
    figure_caption,
    section_context,
    table_caption,
    toc_lines,
)
from metrology_process_planner.reporting.models import ReportDocument, ReportSection, TableModel


@dataclass(frozen=True)
class PdfLine:
    """One styled text line in a PDF content stream."""

    text: str
    size: int = 10
    role: str = "text"
    gap: int = 15


PdfPage = tuple[PdfLine, ...]


def pages_for_document(document: ReportDocument) -> tuple[PdfPage, ...]:
    """Return styled pages for the report."""

    page_count = len(document.sections) + 1
    pages: list[PdfPage] = [_toc_page(document, page_count)]
    for index, section in enumerate(document.sections, start=1):
        pages.append(_section_page(document, section, index + 1, page_count))
    return tuple(pages)


def _toc_page(document: ReportDocument, page_count: int) -> PdfPage:
    lines = [
        PdfLine(document.metadata.title, 18, "accent", 24),
        PdfLine("Table of Contents", 14, "text", 20),
    ]
    lines.extend(PdfLine(item, 10, "text") for item in toc_lines(document))
    lines.append(PdfLine(document_footer(document, 1, page_count), 8, "muted"))
    return tuple(lines)


def _section_page(
    document: ReportDocument,
    section: ReportSection,
    page_number: int,
    page_count: int,
) -> PdfPage:
    lines = [
        PdfLine(document.metadata.title, 9, "muted", 13),
        PdfLine(section.title, 16, "accent", 22),
        PdfLine(section_context(document, section), 8, "muted", 16),
    ]
    lines.extend(PdfLine(item, 10, "text") for item in _wrap_all(section.body))
    lines.extend(_table_lines(table) for table in section.tables)
    lines.extend(_figure_lines(section))
    lines.append(PdfLine(document_footer(document, page_number, page_count), 8, "muted"))
    return tuple(lines[:42])


def _table_lines(table: TableModel) -> PdfLine:
    headers = " | ".join(label for _, label in table.columns)
    rows = "; ".join(
        " | ".join(concise(row.get(key, ""), 28) for key, _ in table.columns)
        for row in table.rows[:3]
    )
    return PdfLine(f"{table_caption(table)} | {headers} | {rows}", 9, "text", 17)


def _figure_lines(section: ReportSection) -> tuple[PdfLine, ...]:
    return tuple(PdfLine(figure_caption(figure), 9, "muted", 17) for figure in section.figures)


def _wrap_all(lines: tuple[str, ...]) -> tuple[str, ...]:
    wrapped: list[str] = []
    for line in lines:
        text = str(line)
        if len(text) <= 92:
            wrapped.append(text)
            continue
        wrapped.extend(text[index : index + 92] for index in range(0, len(text), 92))
    return tuple(wrapped)

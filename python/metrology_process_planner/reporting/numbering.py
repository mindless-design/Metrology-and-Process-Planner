"""Figure, table, and appendix numbering utilities."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.reporting.models import ReportDocument, ReportSection


class ReportNumberer:
    """Assign stable numbers to figures, tables, and appendices."""

    def number(self, document: ReportDocument) -> ReportDocument:
        """Return a copy of the document with numbered section content."""

        figure_number = 0
        table_number = 0
        sections: list[ReportSection] = []
        for section in document.sections:
            tables = []
            for table in section.tables:
                table_number += 1
                tables.append(replace(table, number=table_number))
            figures = []
            for figure in section.figures:
                figure_number += 1
                figures.append(replace(figure, number=figure_number))
            sections.append(replace(section, tables=tuple(tables), figures=tuple(figures)))
        return replace(document, sections=tuple(sections))


def cross_reference_label(kind: str, number: int) -> str:
    """Return a human-readable cross-reference label."""

    labels = {"figure": "Figure", "table": "Table", "appendix": "Appendix"}
    return f"{labels.get(kind, kind.title())} {number}"

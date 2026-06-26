"""OOXML table shape helpers for PowerPoint exports."""

from __future__ import annotations

from xml.sax.saxutils import escape

from metrology_process_planner.reporting.models import TableModel
from metrology_process_planner.reporting.themes import ReportTheme, report_theme


def table_frame(
    table: TableModel,
    shape_id: int,
    y: int,
    theme: ReportTheme | None = None,
) -> str:
    """Return an editable PowerPoint table graphic frame."""

    if not table.columns:
        return ""
    resolved = theme or report_theme("light")
    column_count = len(table.columns)
    rows = (_header_row(table, resolved),) + tuple(
        _data_row(table, row, resolved) for row in table.rows[:8]
    )
    grid = "".join('<a:gridCol w="1400000"/>' for _ in range(column_count))
    return (
        "<p:graphicFrame><p:nvGraphicFramePr>"
        f'<p:cNvPr id="{shape_id}" name="Table {shape_id}"/>'
        "<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>"
        f'<p:xfrm><a:off x="685800" y="{y}"/><a:ext cx="7772400" cy="2200000"/>'
        "</p:xfrm><a:graphic><a:graphicData "
        'uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
        f"<a:tbl><a:tblPr/><a:tblGrid>{grid}</a:tblGrid>{''.join(rows)}</a:tbl>"
        "</a:graphicData></a:graphic></p:graphicFrame>"
    )


def _header_row(table: TableModel, theme: ReportTheme) -> str:
    values = tuple((label, "l") for _, label in table.columns)
    return _row(values, theme, theme.table_header)


def _data_row(table: TableModel, row: dict[str, object], theme: ReportTheme) -> str:
    values = tuple((str(row.get(key, "")), _alignment(key)) for key, _ in table.columns)
    return _row(values, theme, theme.table_row)


def _row(values: tuple[tuple[str, str], ...], theme: ReportTheme, fill: str) -> str:
    cells = "".join(_cell(value, align, theme, fill) for value, align in values)
    return f'<a:tr h="280000">{cells}</a:tr>'


def _cell(value: str, align: str, theme: ReportTheme, fill: str) -> str:
    return (
        f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="{align}"/><a:r>'
        f'<a:rPr sz="1000"><a:solidFill><a:srgbClr val="{theme.text}"/>'
        f"</a:solidFill></a:rPr><a:t>{escape(value)}</a:t>"
        '</a:r></a:p></a:txBody><a:tcPr><a:solidFill>'
        f'<a:srgbClr val="{fill}"/></a:solidFill></a:tcPr></a:tc>'
    )


def _alignment(key: str) -> str:
    return "r" if key in {"length", "target", "lsl", "usl", "measurements", "artifacts"} else "l"

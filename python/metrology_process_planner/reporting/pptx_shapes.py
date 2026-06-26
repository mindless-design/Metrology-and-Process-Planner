"""Reusable themed PowerPoint shape snippets."""

from __future__ import annotations

from xml.sax.saxutils import escape

from metrology_process_planner.reporting.themes import ReportTheme


def slide_wrapper(shapes: str, background: str = "") -> str:
    """Wrap slide shape XML in a presentation slide."""

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<p:cSld>{background}<p:spTree>{shapes}</p:spTree></p:cSld></p:sld>"
    )


def background_shape(theme: ReportTheme) -> str:
    """Return slide background XML."""

    return (
        "<p:bg><p:bgPr>"
        f'<a:solidFill><a:srgbClr val="{theme.background}"/></a:solidFill>'
        "<a:effectLst/></p:bgPr></p:bg>"
    )


def textbox_shape(
    shape_id: int,
    text: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    size: int,
    theme: ReportTheme,
    *,
    name: str = "Text",
    color: str = "",
) -> str:
    """Return an editable themed PowerPoint text box."""

    resolved_color = color or theme.text
    return (
        "<p:sp><p:nvSpPr>"
        f'<p:cNvPr id="{shape_id}" name="{escape(name)} {shape_id}"/>'
        "<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm>"
        f'<a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/>'
        '</a:xfrm></p:spPr><p:txBody><a:bodyPr wrap="square"/>'
        f'<a:lstStyle/><a:p><a:r><a:rPr sz="{size}">'
        f'<a:solidFill><a:srgbClr val="{resolved_color}"/></a:solidFill>'
        f"</a:rPr><a:t>{escape(text)}</a:t></a:r></a:p></p:txBody></p:sp>"
    )


def rule_shape(shape_id: int, x: int, y: int, cx: int, theme: ReportTheme) -> str:
    """Return a slim accent rule."""

    return (
        "<p:sp><p:nvSpPr>"
        f'<p:cNvPr id="{shape_id}" name="Accent Rule {shape_id}"/>'
        "<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm>"
        f'<a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="25400"/>'
        '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:solidFill><a:srgbClr val="{theme.accent}"/></a:solidFill>'
        '<a:ln><a:noFill/></a:ln></p:spPr></p:sp>'
    )

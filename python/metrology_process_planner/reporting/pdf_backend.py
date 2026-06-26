"""Dependency-free PDF backend for printable engineering reports."""

from __future__ import annotations

from pathlib import Path

from metrology_process_planner.reporting.models import ReportDocument
from metrology_process_planner.reporting.pdf_pages import PdfLine, PdfPage, pages_for_document
from metrology_process_planner.reporting.themes import ReportTheme, report_theme


class PdfReportBackend:
    """Export report documents as simple printable PDFs."""

    format_name = "pdf"

    def export(self, document: ReportDocument, destination: Path) -> Path:
        """Write a valid PDF report and return the destination path."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        pages = pages_for_document(document)
        bookmarks = tuple(section.title for section in document.sections)
        theme = report_theme(document.metadata.theme_id)
        destination.write_bytes(_render_pdf(pages, document.metadata.title, bookmarks, theme))
        return destination


def _render_pdf(
    pages: tuple[PdfPage, ...],
    title: str,
    bookmarks: tuple[str, ...],
    theme: ReportTheme,
) -> bytes:
    objects: list[bytes] = [b"", _pages_object(len(pages)), _font_object()]
    page_refs: list[int] = []
    for index, lines in enumerate(pages):
        content_number = 4 + index * 2
        page_number = content_number + 1
        objects.append(_content_object(lines, theme))
        objects.append(_page_object(content_number))
        page_refs.append(page_number)
    outline_ref = len(objects) + 1
    objects[0] = _catalog_object(outline_ref)
    objects[1] = _pages_object(len(pages), page_refs)
    objects.extend(_outline_objects(bookmarks, outline_ref, page_refs))
    objects.append(_info_object(title))
    return _assemble(objects)


def _catalog_object(outline_ref: int) -> bytes:
    return (
        f"<< /Type /Catalog /Pages 2 0 R /Outlines {outline_ref} 0 R "
        "/PageMode /UseOutlines >>"
    ).encode("ascii")


def _pages_object(count: int, refs: list[int] | None = None) -> bytes:
    kids = " ".join(f"{ref} 0 R" for ref in (refs or []))
    return f"<< /Type /Pages /Count {count} /Kids [{kids}] >>".encode("ascii")


def _font_object() -> bytes:
    return b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"


def _outline_objects(
    bookmarks: tuple[str, ...],
    outline_ref: int,
    page_refs: list[int],
) -> list[bytes]:
    if not bookmarks:
        return [b"<< /Type /Outlines /Count 0 >>"]
    first = outline_ref + 1
    last = outline_ref + len(bookmarks)
    root = (
        f"<< /Type /Outlines /First {first} 0 R /Last {last} 0 R "
        f"/Count {len(bookmarks)} >>"
    )
    objects = [root.encode("ascii")]
    for index, title in enumerate(bookmarks):
        objects.append(_outline_item(title, index, len(bookmarks), first, outline_ref, page_refs))
    return objects


def _outline_item(
    title: str,
    index: int,
    bookmark_count: int,
    first_ref: int,
    parent_ref: int,
    page_refs: list[int],
) -> bytes:
    current = first_ref + index
    next_part = f"/Next {current + 1} 0 R " if index < bookmark_count - 1 else ""
    prev_part = f"/Prev {current - 1} 0 R " if index else ""
    page_ref = page_refs[min(index + 1, len(page_refs) - 1)]
    return (
        f"<< /Title ({_escape(title)}) /Parent {parent_ref} 0 R "
        f"{prev_part}{next_part}/Dest [{page_ref} 0 R /Fit] >>"
    ).encode("ascii")


def _page_object(content_number: int) -> bytes:
    return (
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_number} 0 R >>"
    ).encode("ascii")


def _content_object(lines: PdfPage, theme: ReportTheme) -> bytes:
    commands = [*_background_commands(theme)]
    y = 740
    for line in lines:
        commands.extend(_line_commands(line, y, theme))
        y -= line.gap
    stream = "\n".join(commands).encode("ascii", errors="ignore")
    return (
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream"
    )


def _background_commands(theme: ReportTheme) -> list[str]:
    return ["q", _rgb_command(theme.background, "rg"), "0 0 612 792 re f", "Q"]


def _line_commands(line: PdfLine, y: int, theme: ReportTheme) -> list[str]:
    return [
        "BT",
        _rgb_command(_line_color(line, theme), "rg"),
        f"/F1 {line.size} Tf",
        f"72 {y} Td",
        f"({_escape(line.text)}) Tj",
        "ET",
    ]


def _line_color(line: PdfLine, theme: ReportTheme) -> str:
    if line.role == "accent":
        return theme.accent
    if line.role == "muted":
        return theme.muted_text
    return theme.text


def _rgb_command(hex_color: str, operator: str) -> str:
    red = int(hex_color[0:2], 16) / 255
    green = int(hex_color[2:4], 16) / 255
    blue = int(hex_color[4:6], 16) / 255
    return f"{red:.3f} {green:.3f} {blue:.3f} {operator}"


def _info_object(title: str) -> bytes:
    return f"<< /Title ({_escape(title)}) /Producer (Metrology Process Planner) >>".encode("ascii")


def _assemble(objects: list[bytes]) -> bytes:
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_at = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(_trailer(len(offsets), xref_at, len(objects)))
    return bytes(output)


def _trailer(size: int, xref_at: int, info_number: int) -> bytes:
    return (
        f"trailer\n<< /Size {size} /Root 1 0 R /Info {info_number} 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF\n"
    ).encode("ascii")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

"""Dependency-free PowerPoint backend using editable OOXML parts."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from metrology_process_planner.reporting.formatting import (
    document_footer,
    figure_caption,
    section_context,
    table_caption,
)
from metrology_process_planner.reporting.models import ReportDocument, ReportSection
from metrology_process_planner.reporting.pptx_images import (
    SlideImage,
    image_relationships,
    image_shapes,
    placeholder_shapes,
    slide_images,
    slot_geometry,
)
from metrology_process_planner.reporting.pptx_relationships import relationship, rels
from metrology_process_planner.reporting.pptx_shapes import (
    background_shape,
    rule_shape,
    slide_wrapper,
    textbox_shape,
)
from metrology_process_planner.reporting.pptx_static import write_static_parts
from metrology_process_planner.reporting.pptx_tables import table_frame
from metrology_process_planner.reporting.themes import ReportTheme, report_theme


class PowerPointReportBackend:
    """Export report documents as editable PowerPoint presentations."""

    format_name = "pptx"

    def __init__(self, artifact_root: Path | None = None) -> None:
        self._artifact_root = artifact_root

    def export(self, document: ReportDocument, destination: Path) -> Path:
        """Write an editable PPTX deck and return the destination path."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        sections = document.sections or ()
        with ZipFile(destination, "w", ZIP_DEFLATED) as package:
            write_static_parts(package, len(sections))
            theme = report_theme(document.metadata.theme_id)
            for index, section in enumerate(sections, start=1):
                images = slide_images(section, self._artifact_root)
                for image in images:
                    package.write(image.source, f"ppt/{image.package_name}")
                package.writestr(
                    f"ppt/slides/slide{index}.xml",
                    _slide_xml(
                        document,
                        section,
                        images,
                        index,
                        len(sections),
                        self._artifact_root,
                        theme,
                    ),
                )
                package.writestr(
                    f"ppt/notesSlides/notesSlide{index}.xml",
                    _notes_xml(section, theme),
                )
                package.writestr(
                    f"ppt/slides/_rels/slide{index}.xml.rels",
                    _slide_rels(index, image_relationships(images)),
                )
        return destination


def _slide_xml(
    document: ReportDocument,
    section: ReportSection,
    images: tuple[SlideImage, ...],
    slide_number: int,
    slide_count: int,
    artifact_root: Path | None,
    theme: ReportTheme,
) -> str:
    body = "\n".join(section.body + _table_text(section))
    background = background_shape(theme)
    shapes = textbox_shape(1, section.title, 457200, 228600, 8229600, 600000, 3000, theme)
    shapes += rule_shape(2, 457200, 900000, 8229600, theme)
    shapes += textbox_shape(
        3,
        section_context(document, section),
        457200,
        960000,
        8229600,
        260000,
        1100,
        theme,
        name="Section Context",
        color=theme.muted_text,
    )
    shapes += textbox_shape(4, body or " ", 685800, 1300000, 7772400, 1150000, 1600, theme)
    for index, table in enumerate(section.tables[:2], start=3):
        shapes += table_frame(table, index + 10, 2850000 + (index - 3) * 1500000, theme)
    shapes += image_shapes(images)
    shapes += placeholder_shapes(section, artifact_root, theme)
    shapes += _caption_shapes(section, theme)
    shapes += _footer_shape(document, slide_number, slide_count, theme)
    return slide_wrapper(shapes, background)


def _notes_xml(section: ReportSection, theme: ReportTheme) -> str:
    text = textbox_shape(1, "Notes: " + section.title, 0, 0, 6000000, 1000000, 1400, theme)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f"<p:cSld><p:spTree>{text}</p:spTree></p:cSld></p:notes>"
    )


def _slide_rels(index: int, extra_relationships: tuple[str, ...] = ()) -> str:
    return _rels(
        (
            relationship(
                "rId1",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
                f"../notesSlides/notesSlide{index}.xml",
            ),
            *extra_relationships,
        )
    )


def _table_text(section: ReportSection) -> tuple[str, ...]:
    return tuple(table_caption(table) for table in section.tables)


def _caption_shapes(section: ReportSection, theme: ReportTheme) -> str:
    shapes = ""
    for slot, figure in enumerate(section.figures[:4]):
        x, y, cx, cy = slot_geometry(slot)
        shapes += textbox_shape(
            60 + slot,
            figure_caption(figure),
            x,
            y + cy + 35000,
            cx,
            300000,
            950,
            theme,
            name="Figure Caption",
            color=theme.muted_text,
        )
    return shapes


def _footer_shape(
    document: ReportDocument,
    slide_number: int,
    slide_count: int,
    theme: ReportTheme,
) -> str:
    return textbox_shape(
        90,
        document_footer(document, slide_number, slide_count),
        457200,
        6400000,
        8229600,
        240000,
        900,
        theme,
        name="Footer",
        color=theme.muted_text,
    )


def _rels(relationships: tuple[str, ...]) -> str:
    return rels(relationships)

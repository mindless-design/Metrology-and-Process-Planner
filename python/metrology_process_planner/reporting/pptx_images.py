"""OOXML image helpers for PowerPoint exports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from metrology_process_planner.reporting.models import FigureModel, ReportSection
from metrology_process_planner.reporting.themes import ReportTheme, report_theme


@dataclass(frozen=True)
class SlideImage:
    """One image embedded in a PowerPoint slide."""

    rel_id: str
    source: Path
    package_name: str
    title: str
    slot: int = 0


def slide_images(section: ReportSection, artifact_root: Path | None) -> tuple[SlideImage, ...]:
    """Return existing image files that should be embedded in a slide."""

    if artifact_root is None:
        return ()
    images: list[SlideImage] = []
    for index, figure in enumerate(section.figures, start=2):
        source = artifact_root / figure.path if figure.path else None
        if source is None or not source.exists() or figure.placeholder:
            continue
        package_name = f"media/{figure.artifact_id}{source.suffix or '.png'}"
        images.append(SlideImage(f"rId{index}", source, package_name, figure.title, index - 2))
    return tuple(images)


def image_shapes(images: tuple[SlideImage, ...]) -> str:
    """Return editable PowerPoint picture shapes for slide images."""

    return "".join(_picture(image, index) for index, image in enumerate(images[:4], start=20))


def placeholder_shapes(
    section: ReportSection,
    artifact_root: Path | None,
    theme: ReportTheme | None = None,
) -> str:
    """Return visible placeholder boxes for missing slide figures."""

    placeholders = _placeholder_figures(section, artifact_root)
    resolved = theme or report_theme("light")
    return "".join(
        _placeholder(figure, index, slot, resolved)
        for slot, (index, figure) in enumerate(zip(range(40, 44), placeholders[:4]))
    )


def image_relationships(images: tuple[SlideImage, ...]) -> tuple[str, ...]:
    """Return slide relationship XML snippets for embedded images."""

    return tuple(
        (
            f'<Relationship Id="{image.rel_id}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="../{image.package_name}"/>'
        )
        for image in images
    )


def _picture(image: SlideImage, shape_id: int) -> str:
    x, y, cx, cy = slot_geometry(image.slot)
    return (
        "<p:pic><p:nvPicPr>"
        f'<p:cNvPr id="{shape_id}" name="Image {escape(image.title)}"/>'
        "<p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill>"
        f'<a:blip r:embed="{image.rel_id}"/>'
        '<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm>'
        f'<a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/>'
        "</a:xfrm><a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></p:spPr></p:pic>"
    )


def _placeholder_figures(
    section: ReportSection,
    artifact_root: Path | None,
) -> tuple[FigureModel, ...]:
    figures: list[FigureModel] = []
    for figure in section.figures:
        source = artifact_root / figure.path if artifact_root is not None and figure.path else None
        if figure.placeholder or source is None or not source.exists():
            figures.append(figure)
    return tuple(figures)


def _placeholder(figure: FigureModel, shape_id: int, slot: int, theme: ReportTheme) -> str:
    text = _placeholder_text(figure)
    x, y, cx, cy = slot_geometry(slot)
    return (
        "<p:sp><p:nvSpPr>"
        f'<p:cNvPr id="{shape_id}" name="Placeholder {escape(figure.artifact_id)}"/>'
        "<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm>"
        f'<a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/>'
        '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:solidFill><a:srgbClr val="{theme.placeholder_fill}"/></a:solidFill>'
        f'<a:ln w="25400"><a:solidFill><a:srgbClr val="{theme.placeholder_border}"/>'
        "</a:solidFill></a:ln>"
        '</p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>'
        f'<a:p><a:r><a:rPr sz="1400"><a:solidFill><a:srgbClr val="{theme.text}"/>'
        f"</a:solidFill></a:rPr><a:t>{escape(text)}</a:t></a:r></a:p>"
        "</p:txBody></p:sp>"
    )


def _placeholder_text(figure: FigureModel) -> str:
    return (
        f"Missing artifact: {figure.artifact_id}\n"
        f"Expected path: {figure.path}\n"
        f"{figure.notes or 'Regenerate artifact or keep placeholder.'}"
    )


def slot_geometry(slot: int) -> tuple[int, int, int, int]:
    """Return image/placeholder box geometry for a gallery slot."""

    positions = (
        (5486400, 2800000, 2743200, 1580000),
        (685800, 2800000, 2743200, 1580000),
        (5486400, 4750000, 2743200, 1300000),
        (685800, 4750000, 2743200, 1300000),
    )
    return positions[slot % len(positions)]

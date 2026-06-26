"""Static OOXML package parts for PowerPoint report export."""

from __future__ import annotations

from zipfile import ZipFile

from metrology_process_planner.reporting.pptx_relationships import relationship, rels


def write_static_parts(package: ZipFile, slide_count: int) -> None:
    """Write static presentation-level package parts."""

    package.writestr("[Content_Types].xml", _content_types(slide_count))
    package.writestr("_rels/.rels", _root_rels())
    package.writestr("ppt/presentation.xml", _presentation_xml(slide_count))
    package.writestr("ppt/_rels/presentation.xml.rels", _presentation_rels(slide_count))


def _content_types(slide_count: int) -> str:
    overrides = [
        _override(
            "/ppt/presentation.xml",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
        )
    ]
    for index in range(1, slide_count + 1):
        overrides.append(
            _override(
                f"/ppt/slides/slide{index}.xml",
                "application/vnd.openxmlformats-officedocument.presentationml.slide+xml",
            )
        )
        overrides.append(
            _override(
                f"/ppt/notesSlides/notesSlide{index}.xml",
                "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
            )
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        + "".join(overrides)
        + "</Types>"
    )


def _root_rels() -> str:
    return rels(
        (
            relationship(
                "rId1",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
                "ppt/presentation.xml",
            ),
        )
    )


def _presentation_xml(slide_count: int) -> str:
    ids = "".join(
        f'<p:sldId id="{255 + index}" r:id="rId{index}"/>'
        for index in range(1, slide_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<p:sldIdLst>{ids}</p:sldIdLst>"
        '<p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>'
        "</p:presentation>"
    )


def _presentation_rels(slide_count: int) -> str:
    return rels(
        tuple(
            relationship(
                f"rId{index}",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
                f"slides/slide{index}.xml",
            )
            for index in range(1, slide_count + 1)
        )
    )


def _override(part_name: str, content_type: str) -> str:
    return f'<Override PartName="{part_name}" ContentType="{content_type}"/>'

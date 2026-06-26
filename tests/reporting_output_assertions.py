import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

SLIDE_WIDTH = 9144000
SLIDE_HEIGHT = 6858000


@dataclass(frozen=True)
class Box:
    name: str
    x: int
    y: int
    width: int
    height: int

    def overlaps(self, other: "Box") -> bool:
        return not (
            self.x + self.width <= other.x
            or other.x + other.width <= self.x
            or self.y + self.height <= other.y
            or other.y + other.height <= self.y
        )


def pptx_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as package:
        return set(package.namelist())


def slide_xml(path: Path, slide_number: int) -> bytes:
    with zipfile.ZipFile(path) as package:
        return package.read(f"ppt/slides/slide{slide_number}.xml")


def slide_text(path: Path, slide_number: int) -> str:
    root = ElementTree.fromstring(slide_xml(path, slide_number))
    return "\n".join(node.text or "" for node in root.iter() if _local(node.tag) == "t")


def slide_boxes(path: Path, slide_number: int) -> tuple[Box, ...]:
    root = ElementTree.fromstring(slide_xml(path, slide_number))
    boxes = []
    for element in root.iter():
        if _local(element.tag) not in {"sp", "pic", "graphicFrame"}:
            continue
        name = _shape_name(element)
        if name == "Theme Background":
            continue
        off, ext = _xfrm_parts(element)
        if off is not None and ext is not None:
            boxes.append(
                Box(name, _int(off, "x"), _int(off, "y"), _int(ext, "cx"), _int(ext, "cy"))
            )
    return tuple(boxes)


def assert_boxes_inside_slide(testcase, boxes: tuple[Box, ...]) -> None:
    for box in boxes:
        testcase.assertGreaterEqual(box.x, 0, box)
        testcase.assertGreaterEqual(box.y, 0, box)
        testcase.assertLessEqual(box.x + box.width, SLIDE_WIDTH, box)
        testcase.assertLessEqual(box.y + box.height, SLIDE_HEIGHT, box)


def assert_no_box_overlaps(testcase, boxes: tuple[Box, ...]) -> None:
    content_boxes = tuple(box for box in boxes if box.name != "Theme Background")
    for index, box in enumerate(content_boxes):
        for other in content_boxes[index + 1 :]:
            testcase.assertFalse(box.overlaps(other), f"{box} overlaps {other}")


def assert_pptx_relationships_resolve(testcase, path: Path) -> None:
    names = pptx_names(path)
    with zipfile.ZipFile(path) as package:
        rel_names = [name for name in names if name.endswith(".rels")]
        for rel_name in rel_names:
            root = ElementTree.fromstring(package.read(rel_name))
            for rel in root:
                target = rel.attrib.get("Target", "")
                if target.startswith("http") or not target:
                    continue
                testcase.assertIn(_resolve_target(rel_name, target), names)


def placeholder_boxes(path: Path, slide_number: int) -> tuple[Box, ...]:
    return tuple(
        box for box in slide_boxes(path, slide_number) if box.name.startswith("Placeholder")
    )


def _shape_name(element: ElementTree.Element) -> str:
    for child in element.iter():
        if _local(child.tag) == "cNvPr":
            return child.attrib.get("name", "")
    return ""


def _xfrm_parts(
    element: ElementTree.Element,
) -> tuple[ElementTree.Element | None, ElementTree.Element | None]:
    for child in element.iter():
        if _local(child.tag) != "xfrm":
            continue
        off = next((item for item in child if _local(item.tag) == "off"), None)
        ext = next((item for item in child if _local(item.tag) == "ext"), None)
        return off, ext
    return None, None


def _resolve_target(rel_name: str, target: str) -> str:
    base = PurePosixPath(rel_name.replace("\\", "/")).parent
    if base.name == "_rels":
        base = base.parent
    return _normalize(base / target)


def _normalize(path: PurePosixPath) -> str:
    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def _int(element: ElementTree.Element, key: str) -> int:
    return int(element.attrib.get(key, "0"))


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]

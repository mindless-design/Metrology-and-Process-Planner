"""SVG renderer for overview diagram scenes."""

from __future__ import annotations

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.rendering.overview.geometry import box_union
from metrology_process_planner.rendering.overview.models import (
    LabelBox,
    LabelTarget,
    LeaderPath,
    OverviewDiagramScene,
    OverviewStylePolicy,
)
from metrology_process_planner.rendering.svg_text import hidden_text_element, text_image_element


class OverviewDiagramRenderer:
    """Render overview scenes into report-ready SVG image artifacts."""

    def render_svg(
        self,
        scene: OverviewDiagramScene,
        style: OverviewStylePolicy | None = None,
    ) -> str:
        """Return deterministic SVG text for an overview diagram scene."""

        style = style or OverviewStylePolicy()
        view = _view_bounds(scene)
        return "\n".join(
            (
                '<?xml version="1.0" encoding="UTF-8"?>',
                _svg_open(view),
                _background(view, style),
                _title(scene, view, style),
                *(_target_svg(target, style) for target in scene.target_shapes),
                *(_leader_svg(leader, style) for leader in scene.leader_paths),
                *(_label_svg(label, style) for label in scene.label_boxes),
                "</svg>",
            )
        ) + "\n"


def _view_bounds(scene: OverviewDiagramScene) -> Box:
    boxes = [scene.layout_bounds]
    boxes.extend(label.bounds for label in scene.label_boxes)
    boxes.extend(target.bbox for target in scene.target_shapes)
    view = box_union(boxes)
    return Box(view.left, view.bottom, view.right, view.top + 36.0)


def _svg_open(view: Box) -> str:
    width = max(1, int(view.width))
    height = max(1, int(view.height))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" '
        f'viewBox="{_num(view.left)} {_num(view.bottom)} {width} {height}" role="img">'
    )


def _background(view: Box, style: OverviewStylePolicy) -> str:
    return (
        f'<rect x="{_num(view.left)}" y="{_num(view.bottom)}" '
        f'width="{_num(view.width)}" height="{_num(view.height)}" '
        f'fill="{style.background_style}" />'
    )


def _title(scene: OverviewDiagramScene, view: Box, style: OverviewStylePolicy) -> str:
    return (
        _text_pair(scene.title, view.left + 12, view.top - 14, 20, style.text_style,
                   ' font-weight="700"')
    )


def _target_svg(target: LabelTarget, style: OverviewStylePolicy) -> str:
    box = target.bbox.normalized()
    stroke = style.warning_target_style if target.warning_ids else _target_color(target, style)
    return (
        f'<rect x="{_num(box.left)}" y="{_num(box.bottom)}" '
        f'width="{_num(box.width)}" height="{_num(box.height)}" '
        f'fill="none" stroke="{stroke}" stroke-width="3" opacity="0.95" />'
    )


def _leader_svg(leader: LeaderPath, style: OverviewStylePolicy) -> str:
    points = " ".join(f"{_num(point.x)},{_num(point.y)}" for point in leader.points)
    return (
        f'<polyline points="{points}" fill="none" stroke="{style.leader_style}" '
        'stroke-width="2.4" opacity="0.9" />'
    )


def _label_svg(label: LabelBox, style: OverviewStylePolicy) -> str:
    box = label.bounds.normalized()
    lines = [
        f'<rect x="{_num(box.left)}" y="{_num(box.bottom)}" width="{_num(box.width)}" '
        f'height="{_num(box.height)}" rx="4" ry="4" fill="{style.label_box_style}" '
        f'stroke="{style.leader_style}" stroke-width="1.2" opacity="0.92" />'
    ]
    for index, text in enumerate(label.text_lines):
        weight = " font-weight=\"700\"" if index == 0 else ""
        fill = style.text_style if index == 0 else style.secondary_text_style
        size = 14 if index == 0 else 13
        lines.append(_text_pair(text, box.left + 8, box.bottom + 16 + index * 15,
                                size, fill, weight))
    return "\n".join(lines)


def _target_color(target: LabelTarget, style: OverviewStylePolicy) -> str:
    colors = dict(style.color_policy or {})
    defaults = {
        "measurement": "#22d3ee",
        "profilometry_line": "#c084fc",
        "ellipsometry_point": "#86efac",
        "fib_cut_line": "#fb923c",
        "user_label": "#facc15",
    }
    return colors.get(target.label_role, defaults.get(target.target_type, style.target_box_style))


def _num(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _text_pair(
    text: str,
    x: float,
    y: float,
    font_size_px: float,
    fill: str,
    weight: str = "",
) -> str:
    return "\n".join(
        (
            text_image_element(text, x, y, font_size_px, fill),
            hidden_text_element(text, x, y, font_size_px, fill, weight=weight),
        )
    )

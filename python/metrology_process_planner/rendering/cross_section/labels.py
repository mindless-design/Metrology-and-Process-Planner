"""Label candidate generation and simple collision-aware placement."""

from __future__ import annotations

from metrology_process_planner.rendering.cross_section.models import LabelPolicy
from metrology_process_planner.rendering.cross_section.scene_models import (
    LabelCandidate,
    MaterialShape,
    PlacedLabel,
)


def build_label_candidates(
    shapes: tuple[MaterialShape, ...],
    policy: LabelPolicy,
) -> tuple[LabelCandidate, ...]:
    """Build material label candidates from projected shapes."""

    if not policy.show_material_labels:
        return ()
    candidates: list[LabelCandidate] = []
    for shape in _representative_shapes(shapes):
        thickness = abs(shape.physical_bounds[3] - shape.physical_bounds[1])
        text = shape.material_name
        if policy.show_thickness:
            text = f"{text}, {thickness:g} nm"
        priority = _priority(shape)
        inline = policy.allow_inline and not shape.thin_layer_flag
        candidates.append(
            LabelCandidate(
                shape.shape_id,
                text,
                priority,
                ("inline", "right_margin", "legend"),
                ("inline", "leader", "callout", "legend_only"),
                _anchor(shape),
                leader_allowed=policy.allow_leaders,
                inline_allowed=inline,
            )
        )
    return tuple(sorted(candidates, key=lambda item: item.priority, reverse=True))


def _representative_shapes(shapes: tuple[MaterialShape, ...]) -> tuple[MaterialShape, ...]:
    best: dict[str, MaterialShape] = {}
    for shape in shapes:
        if not shape.visible:
            continue
        current = best.get(shape.material_id)
        if current is None or _shape_score(shape) > _shape_score(current):
            best[shape.material_id] = shape
    return tuple(best.values())


def _shape_score(shape: MaterialShape) -> tuple[int, float]:
    return (_priority(shape), _area(shape.visual_bounds))


def place_labels(
    candidates: tuple[LabelCandidate, ...],
    shapes: tuple[MaterialShape, ...],
    policy: LabelPolicy,
    scene_bounds: tuple[float, float, float, float],
) -> tuple[PlacedLabel, ...]:
    """Place labels using deterministic priority and rectangle collision checks."""

    shape_lookup = {shape.shape_id: shape for shape in shapes}
    placed: list[PlacedLabel] = []
    occupied: list[tuple[float, float, float, float]] = []
    right_x = scene_bounds[2] + max((scene_bounds[2] - scene_bounds[0]) * 0.05, 20.0)
    lane = 0
    for candidate in candidates:
        label, lane = _place_candidate(candidate, shape_lookup, policy, occupied, right_x, lane)
        if label is None:
            continue
        placed.append(label)
        if label.placement_type != "legend_only":
            occupied.append(label.bounding_box)
    return tuple(placed)


def _place_candidate(
    candidate: LabelCandidate,
    shape_lookup: dict[str, MaterialShape],
    policy: LabelPolicy,
    occupied: list[tuple[float, float, float, float]],
    right_x: float,
    lane: int,
) -> tuple[PlacedLabel | None, int]:
    shape = shape_lookup.get(candidate.target_id)
    if shape is None:
        return None, lane
    inline = _inline_label(candidate, shape)
    if candidate.inline_allowed and not any(
        _overlaps(inline.bounding_box, item) for item in occupied
    ):
        return inline, lane
    leader, lane = _leader_candidate(candidate, policy, occupied, right_x, lane)
    if leader is not None:
        return leader, lane
    if policy.allow_callouts and candidate.priority >= 80:
        return _callout_label(candidate, right_x, lane), lane + 1
    return _legend_only_label(candidate), lane


def _leader_candidate(
    candidate: LabelCandidate,
    policy: LabelPolicy,
    occupied: list[tuple[float, float, float, float]],
    right_x: float,
    lane: int,
) -> tuple[PlacedLabel | None, int]:
    if not policy.allow_leaders or not candidate.leader_allowed:
        return None, lane
    leader = _leader_label(candidate, right_x, lane)
    lane += 1
    if any(_overlaps(leader.bounding_box, item) for item in occupied):
        return None, lane
    return leader, lane


def labels_have_collisions(labels: tuple[PlacedLabel, ...]) -> bool:
    """Return whether any placed labels still overlap."""

    boxes = [label.bounding_box for label in labels if label.placement_type != "legend_only"]
    return any(_overlaps(left, right) for index, left in enumerate(boxes)
               for right in boxes[index + 1:])


def _priority(shape: MaterialShape) -> int:
    if shape.exaggerated_flag or shape.thin_layer_flag:
        return 90
    if shape.compressed_flag:
        return 60
    if shape.material_id.lower() in {"si", "substrate"}:
        return 20
    return 50


def _anchor(shape: MaterialShape) -> tuple[float, float]:
    left, bottom, right, top = shape.visual_bounds
    return ((left + right) / 2.0, (bottom + top) / 2.0)


def _area(bounds: tuple[float, float, float, float]) -> float:
    left, bottom, right, top = bounds
    return max(0.0, right - left) * max(0.0, top - bottom)


def _inline_label(candidate: LabelCandidate, shape: MaterialShape) -> PlacedLabel:
    anchor = _anchor(shape)
    width = _text_width(candidate.text)
    height = 14.0
    box = (anchor[0] - width / 2.0, anchor[1] - height / 2.0, width, height)
    return PlacedLabel(
        f"label-{candidate.target_id}",
        candidate.target_id,
        candidate.text,
        anchor,
        candidate.anchor_point,
        "inline",
        box,
        priority=candidate.priority,
    )


def _leader_label(candidate: LabelCandidate, right_x: float, lane: int) -> PlacedLabel:
    y = candidate.anchor_point[1] + (lane * 18.0)
    width = _text_width(candidate.text)
    box = (right_x, y - 7.0, width, 14.0)
    return PlacedLabel(
        f"label-{candidate.target_id}",
        candidate.target_id,
        candidate.text,
        (right_x, y),
        candidate.anchor_point,
        "leader",
        box,
        (candidate.anchor_point, (right_x, y)),
        candidate.priority,
    )


def _callout_label(candidate: LabelCandidate, right_x: float, lane: int) -> PlacedLabel:
    y = candidate.anchor_point[1] + (lane * 18.0)
    width = _text_width(candidate.text) + 16.0
    box = (right_x, y - 10.0, width, 20.0)
    return PlacedLabel(
        f"label-{candidate.target_id}",
        candidate.target_id,
        candidate.text,
        (right_x + 8.0, y),
        candidate.anchor_point,
        "callout",
        box,
        (candidate.anchor_point, (right_x, y)),
        candidate.priority,
    )


def _legend_only_label(candidate: LabelCandidate) -> PlacedLabel:
    return PlacedLabel(
        f"label-{candidate.target_id}",
        candidate.target_id,
        candidate.text,
        candidate.anchor_point,
        candidate.anchor_point,
        "legend_only",
        (0.0, 0.0, 0.0, 0.0),
        priority=candidate.priority,
        collision_status="fallback",
    )


def _text_width(text: str) -> float:
    return max(28.0, len(text) * 6.5)

def _overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and a[1] < b[1] + b[3] and a[1] + a[3] > b[1]

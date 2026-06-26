"""Small scene assembly helpers for cross-section pipeline output."""

from __future__ import annotations

import math

from metrology_process_planner.domains.process import ProcessFrame
from metrology_process_planner.domains.session.display_units import (
    convert_length,
    format_length,
    resolved_display_unit,
)
from metrology_process_planner.rendering.cross_section.models import RenderIntent, RenderProfile
from metrology_process_planner.rendering.cross_section.scene_models import (
    CrossSectionSceneModel,
    LegendEntry,
    LegendModel,
    MaterialShape,
    PlacedLabel,
)


def axes(
    profile: RenderProfile,
    physical_bounds: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
    canonical_units: str = "um",
    display_unit_preference: str = "auto",
) -> tuple[dict[str, object], ...]:
    """Return axis metadata for a render profile."""

    if profile.axis_policy == "none":
        return ()
    units = _axis_units(display_unit_preference, _range_size(physical_bounds), canonical_units)
    x_range = (float(physical_bounds[0]), float(physical_bounds[2]))
    z_range = (float(physical_bounds[1]), float(physical_bounds[3]))
    return (
        _axis("x", "x distance", x_range, canonical_units, units),
        _axis("z", "height", z_range, canonical_units, units),
    )


def scale_bars(
    profile: RenderProfile,
    physical_bounds: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
    canonical_units: str = "um",
    display_unit_preference: str = "auto",
) -> tuple[dict[str, object], ...]:
    """Return scale bars required by physical render modes."""

    if profile.render_mode_id != "proportional_physical":
        return ()
    length = _nice_step(max(0.001, (physical_bounds[2] - physical_bounds[0]) / 4.0))
    units = _axis_units(display_unit_preference, _range_size(physical_bounds), canonical_units)
    return (
        {
            "length": length,
            "units": units,
            "label": format_length(length, canonical_units, units),
        },
    )


def leaders(labels: tuple[PlacedLabel, ...]) -> tuple[dict[str, object], ...]:
    """Return leader-line scene metadata from placed labels."""

    return tuple(
        {"target_id": label.target_id, "points": label.leader_line}
        for label in labels
        if getattr(label, "leader_line", None)
    )


def callouts(labels: tuple[PlacedLabel, ...]) -> tuple[dict[str, object], ...]:
    """Return callout scene metadata from placed labels."""

    return tuple(
        {"target_id": label.target_id, "text": label.text}
        for label in labels
        if getattr(label, "placement_type", "") == "callout"
    )


def legend(shapes: tuple[MaterialShape, ...], profile: RenderProfile) -> LegendModel:
    """Build a material legend for visible scene shapes."""

    entries: dict[str, LegendEntry] = {}
    for shape in shapes:
        if shape.material_id in entries:
            continue
        notes = ("exaggerated",) if shape.exaggerated_flag else ()
        entries[shape.material_id] = LegendEntry(
            shape.material_id,
            shape.material_name,
            shape.visual_style.get("fill", "#888888"),
            notes,
        )
    return LegendModel(
        tuple(entries.values()),
        compact=profile.legend_policy == "compact",
        show_exaggeration_notes=profile.thin_layer_policy.show_exaggeration_note,
        show_compression_notes=profile.compression_policy.show_compression_legend,
    )


def step_annotations(frame: ProcessFrame, profile: RenderProfile) -> tuple[dict[str, object], ...]:
    """Return step annotations for process-flow style scenes."""

    if not profile.label_policy.show_step_labels:
        return ()
    return ({"kind": "step_label", "step_id": frame.step_id, "text": frame.title},)


def highlights(intent: RenderIntent) -> tuple[dict[str, object], ...]:
    """Return selected-step highlight metadata."""

    if not intent.selected_process_step_id:
        return ()
    return (
        {
            "kind": intent.highlight_policy or "selected_step",
            "step_id": intent.selected_process_step_id,
        },
    )


def empty_scene(
    scene_id: str,
    profile: RenderProfile,
    title: str,
    warnings: tuple[str, ...],
) -> CrossSectionSceneModel:
    """Return a valid placeholder scene for empty solver output."""

    return CrossSectionSceneModel(
        scene_id,
        profile.render_mode_id,
        title or profile.display_name,
        "um",
        "px",
        {},
        (),
        warnings=warnings,
    )


def _axis(
    orientation: str,
    name: str,
    physical_range: tuple[float, float],
    canonical_units: str,
    units: str,
) -> dict[str, object]:
    ticks = tuple(_ticks(physical_range))
    return {
        "orientation": orientation,
        "axis": orientation,
        "label": f"{name} ({units})",
        "unit": units,
        "units": units,
        "physical_range": physical_range,
        "ticks": tuple(
            {
                "value": value,
                "label": format_length(value, canonical_units, units),
                "position": value,
            }
            for value in ticks
        ),
    }


def _ticks(physical_range: tuple[float, float], target_count: int = 5) -> tuple[float, ...]:
    start, stop = sorted((float(physical_range[0]), float(physical_range[1])))
    span = stop - start
    if span <= 0:
        return (start,)
    step = _nice_step(span / max(1, target_count - 1))
    first = _ceil_to_step(start, step)
    values: list[float] = []
    current = first
    while current <= stop + step * 0.25 and len(values) < target_count + 2:
        values.append(round(current, 9))
        current += step
    if not values:
        values.append(start)
    return tuple(values)


def _nice_step(raw: float) -> float:
    if raw <= 0:
        return 1.0
    exponent = float(10 ** int(math.floor(math.log10(raw))))
    fraction = raw / exponent
    if fraction <= 1:
        nice = 1
    elif fraction <= 2:
        nice = 2
    elif fraction <= 5:
        nice = 5
    else:
        nice = 10
    return nice * exponent


def _ceil_to_step(value: float, step: float) -> float:
    return math.ceil(value / step) * step


def _range_size(physical_bounds: tuple[float, float, float, float]) -> float:
    x_span = abs(float(physical_bounds[2]) - float(physical_bounds[0]))
    z_span = abs(float(physical_bounds[3]) - float(physical_bounds[1]))
    return max(x_span, z_span)
def _axis_units(
    display_unit_preference: str, span: float = 0.0, canonical_units: str = "um"
) -> str:
    if not display_unit_preference or display_unit_preference == "auto":
        span_um = convert_length(span, canonical_units, "um")
        return "nm" if span_um and span_um < 10.0 else "um"
    return resolved_display_unit(None, canonical_units, display_unit_preference)

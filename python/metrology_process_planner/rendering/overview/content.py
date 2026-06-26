"""Compact overview label content generation."""

from __future__ import annotations

from metrology_process_planner.rendering.overview.models import LabelContent, LabelTarget


def build_label_content(
    targets: tuple[LabelTarget, ...],
    detail_level: str = "standard",
) -> tuple[LabelContent, ...]:
    """Build label text for each target using role-aware but mode-neutral rules."""

    return tuple(_content_for_target(target, detail_level) for target in targets)


def _content_for_target(target: LabelTarget, detail_level: str) -> LabelContent:
    metadata = dict(target.metadata or {})
    if target.label_role == "measurement":
        return _measurement_content(target, metadata, detail_level)
    if target.label_role == "user_label":
        return _user_content(target, metadata, detail_level)
    return _capture_content(target, metadata, detail_level)


def _capture_content(
    target: LabelTarget,
    metadata: dict[str, object],
    detail_level: str,
) -> LabelContent:
    sequence = _int_value(metadata.get("sequence"))
    title = (
        f"Site {sequence:02d}"
        if sequence
        else str(metadata.get("label") or target.source_item_id)
    )
    subtitle = str(metadata.get("label") or "") if sequence else ""
    details = _details(detail_level, str(metadata.get("notes") or ""), target.warning_ids)
    return LabelContent(
        f"label-{target.target_id}",
        target.target_id,
        title,
        subtitle,
        details,
        badges=("warning",) if target.warning_ids else (),
        severity="warning" if target.warning_ids else "",
        priority=target.priority,
    )


def _measurement_content(
    target: LabelTarget,
    metadata: dict[str, object],
    detail_level: str,
) -> LabelContent:
    title = str(metadata.get("label") or target.source_item_id)
    subtitle = _measurement_subtitle(metadata)
    details = _details(detail_level, str(metadata.get("notes") or ""), target.warning_ids)
    return LabelContent(
        f"label-{target.target_id}",
        target.target_id,
        title,
        subtitle,
        details,
        badges=("warning",) if target.warning_ids else (),
        severity="warning" if target.warning_ids else "",
        priority=target.priority,
    )


def _user_content(
    target: LabelTarget,
    metadata: dict[str, object],
    detail_level: str,
) -> LabelContent:
    notes = str(metadata.get("notes") or "")
    return LabelContent(
        f"label-{target.target_id}",
        target.target_id,
        str(metadata.get("title") or target.source_item_id),
        "",
        _details(detail_level, notes, target.warning_ids),
        badges=("warning",) if target.warning_ids else (),
        severity="warning" if target.warning_ids else "",
        priority=target.priority,
    )


def _measurement_subtitle(metadata: dict[str, object]) -> str:
    target = metadata.get("target")
    if target is None:
        return ""
    return f"{_float_value(target):.3g} um target"


def _details(detail_level: str, notes: str, warning_ids: tuple[str, ...]) -> tuple[str, ...]:
    if detail_level == "minimal":
        return ()
    details: list[str] = []
    if detail_level in {"detailed", "debug"} and notes:
        details.append(notes)
    if warning_ids and detail_level in {"standard", "detailed", "debug"}:
        details.append("Warning attached")
    if detail_level == "debug":
        details.extend(warning_ids)
    return tuple(details)


def _int_value(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value or "0")
    if hasattr(value, "__int__"):
        return int(value)
    return 0


def _float_value(value: object) -> float:
    if isinstance(value, (float, int, str)):
        return float(value)
    if hasattr(value, "__float__"):
        return float(value)
    return 0.0

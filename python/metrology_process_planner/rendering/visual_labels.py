"""Shared label contracts and capture label content builders."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import CaptureRecord, SessionRecord


@dataclass(frozen=True)
class LabelStylePolicy:
    """Reusable visual style policy for generated artifact labels."""

    font_family: str = "Arial, sans-serif"
    font_size: int = 14
    min_font_size: int = 10
    text_color: str = "#0f172a"
    background_color: str = "#ffffff"
    border_color: str = "#334155"
    opacity: float = 0.94
    padding_px: int = 10
    corner_radius_px: int = 4
    leader_style: str = "#475569"

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible style policy data."""

        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "min_font_size": self.min_font_size,
            "text_color": self.text_color,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "opacity": self.opacity,
            "padding_px": self.padding_px,
            "corner_radius_px": self.corner_radius_px,
            "leader_style": self.leader_style,
        }


@dataclass(frozen=True)
class LabelSpec:
    """Renderer-neutral label request shared by site, overview, and stack artifacts."""

    label_id: str
    text_lines: tuple[str, ...]
    target_ref: str
    priority: int = 50
    style: LabelStylePolicy = LabelStylePolicy()
    placement_policy: str = "auto"
    leader_policy: str = "auto"
    max_width_px: int = 240
    warning_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible label request data."""

        return {
            "label_id": self.label_id,
            "text_lines": list(self.text_lines),
            "target_ref": self.target_ref,
            "priority": self.priority,
            "style": self.style.to_dict(),
            "placement_policy": self.placement_policy,
            "leader_policy": self.leader_policy,
            "max_width_px": self.max_width_px,
            "warning_ids": list(self.warning_ids),
        }


class SiteLabelBuilder:
    """Build report-ready default label text from capture and mode metadata."""

    def build(
        self,
        session: SessionRecord,
        capture: CaptureRecord,
        detail_level: str = "standard",
    ) -> LabelSpec:
        """Return a shared label spec for one saved capture."""

        lines = _trim_empty(_title_line(session, capture), _subtitle_line(capture))
        if detail_level in {"standard", "detailed", "debug"}:
            lines += _geometry_lines(capture)
        if detail_level in {"detailed", "debug"} and capture.notes:
            lines += (capture.notes,)
        if detail_level == "debug":
            lines += (f"id: {capture.id}", f"type: {capture.type}")
        return LabelSpec(
            label_id=f"label-{capture.id}",
            text_lines=lines or (capture.label or capture.id,),
            target_ref=f"capture:{capture.id}",
            priority=80 if capture.warning_ids else 60,
            placement_policy="title_strip",
            leader_policy="none",
            warning_ids=capture.warning_ids,
        )


def capture_bounds_summary(capture: CaptureRecord) -> str:
    """Return a compact extents summary for a capture."""

    bounds = capture.geometry.bounds
    if bounds is None:
        return ""
    box = bounds.normalized()
    return f"Size: {_fmt(box.width)} x {_fmt(box.height)} um"


def capture_center_summary(capture: CaptureRecord) -> str:
    """Return a compact center-coordinate summary for a capture."""

    box = _capture_box(capture)
    if box is None:
        return ""
    center = box.center
    return f"Center: ({_fmt(center.x)} um, {_fmt(center.y)} um)"


def _title_line(session: SessionRecord, capture: CaptureRecord) -> str:
    metadata = dict(capture.metadata or {})
    feature = _primary_feature(capture)
    issue = metadata.get("issue_id") or metadata.get("issue_number")
    category = metadata.get("category") or metadata.get("issue_category")
    if _is_cad_review_capture(capture, issue):
        prefix = f"Issue {_seq(capture, issue)}"
        return f"{prefix} - {category}" if category else prefix
    kind = f"{feature.get('kind', '')} {feature.get('role', '')}"
    if _is_profile_capture(capture, kind):
        return f"Profile Site {_seq(capture)}"
    if _is_film_capture(capture, kind):
        return f"Film Site {_seq(capture)}"
    if _is_fib_capture(capture, kind):
        return f"FIB Cut {_seq(capture)}"
    if _is_cdsem_capture(session, capture):
        return f"CDSEM Site {_seq(capture)}"
    return f"Site {_seq(capture)}"


def _is_cad_review_capture(capture: CaptureRecord, issue: object) -> bool:
    return capture.role == "cad_review" or capture.type == "cad_review_issue" or bool(issue)


def _is_profile_capture(capture: CaptureRecord, kind: str) -> bool:
    return "profilometry" in kind or capture.type == "profilometry"


def _is_film_capture(capture: CaptureRecord, kind: str) -> bool:
    return "ellipsometry" in kind or capture.type == "ellipsometry"


def _is_fib_capture(capture: CaptureRecord, kind: str) -> bool:
    return "fib" in kind or capture.type == "fib"


def _is_cdsem_capture(session: SessionRecord, capture: CaptureRecord) -> bool:
    return "cdsem" in session.mode.value or capture.type == "cdsem"


def _subtitle_line(capture: CaptureRecord) -> str:
    metadata = dict(capture.metadata or {})
    feature = _primary_feature(capture)
    if (capture.role == "cad_review" or capture.type == "cad_review_issue") and capture.notes:
        return capture.notes
    for key in (
        "feature_type",
        "film_target",
        "cut_purpose",
        "issue_summary",
        "description",
    ):
        value = str(metadata.get(key, "")).strip()
        if value:
            return value
    return str(feature.get("label") or capture.label or capture.notes or "").strip()


def _geometry_lines(capture: CaptureRecord) -> tuple[str, ...]:
    return _trim_empty(capture_center_summary(capture), capture_bounds_summary(capture))


def _primary_feature(capture: CaptureRecord) -> Mapping[str, Any]:
    if capture.geometry.features:
        feature = capture.geometry.features[0]
        if isinstance(feature, Mapping):
            return feature
    return {}


def _capture_box(capture: CaptureRecord) -> Box | None:
    if capture.geometry.bounds is not None:
        return capture.geometry.bounds.normalized()
    return None


def _seq(capture: CaptureRecord, fallback: object = "") -> str:
    value = fallback or capture.sequence or capture.id.rsplit("-", 1)[-1]
    if isinstance(value, int):
        return f"{value:03d}"
    text = str(value)
    return f"{int(text):03d}" if text.isdigit() else text


def _trim_empty(*lines: str) -> tuple[str, ...]:
    return tuple(line for line in lines if line)


def _fmt(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")

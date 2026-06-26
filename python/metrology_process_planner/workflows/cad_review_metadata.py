"""CAD review metadata normalization for recipe-free review captures."""

from __future__ import annotations

from metrology_process_planner.domains.modes.mode_non_process_vocab import (
    CAD_REVIEW_CATEGORIES,
    CAD_REVIEW_SEVERITIES,
)


def normalized_cad_review_metadata(metadata: dict[str, object]) -> dict[str, object]:
    """Return CAD review metadata with stable category and severity values."""

    normalized = dict(metadata)
    normalized["review_category"] = normalized_review_category(
        str(normalized.get("review_category", ""))
    )
    severity = str(normalized.get("severity", "")).strip().lower()
    normalized["severity"] = severity if severity in CAD_REVIEW_SEVERITIES else "medium"
    return normalized


def normalized_review_category(value: str) -> str:
    """Return a supported CAD review category, defaulting unsupported values to other."""

    category = value.strip().lower().replace(" ", "_").replace("-", "_")
    if category in CAD_REVIEW_CATEGORIES:
        return category
    return "other" if category else "layout_issue"

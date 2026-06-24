"""Canonical artifact identifier helpers."""

from __future__ import annotations


def artifact_id(owner_type: str, owner_id: str, role: str) -> str:
    """Return a deterministic artifact id for an owner and role."""

    return _safe_id(f"{owner_type}-{owner_id}-{role}") or "artifact"


def _safe_id(text: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_" else "-" for char in text)
    return cleaned.strip("-").lower()

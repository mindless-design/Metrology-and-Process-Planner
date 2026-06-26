"""Artifact content-type inference helpers."""

from __future__ import annotations

_CONTENT_TYPES = {
    "svg": "image/svg+xml",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "json": "application/json",
    "csv": "text/csv",
    "ppt": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def artifact_content_type(path: str) -> str:
    """Return a best-effort content type for a session artifact path."""

    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return _CONTENT_TYPES.get(suffix, "")

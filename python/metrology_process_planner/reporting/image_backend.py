"""Image package backend for report artifact bundles."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from metrology_process_planner.reporting.models import ArtifactSummary, ReportDocument


class ImagePackageBackend:
    """Export report figure references as a portable image package."""

    format_name = "images.zip"

    def __init__(self, artifact_root: Path | None = None) -> None:
        self._artifact_root = artifact_root

    def export(self, document: ReportDocument, destination: Path) -> Path:
        """Write a zip package with image files or placeholder manifests."""

        destination.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(destination, "w", ZIP_DEFLATED) as package:
            for artifact in document.artifacts:
                if not _is_image_artifact(artifact.artifact_type, artifact.role):
                    continue
                source = _source_path(self._artifact_root, artifact.relative_path)
                if source is not None and source.exists():
                    package.write(source, f"images/{source.name}")
                else:
                    placeholder_name = f"placeholders/{artifact.artifact_id}.txt"
                    package.writestr(placeholder_name, _placeholder(artifact))
        return destination


def _is_image_artifact(artifact_type: str, role: str) -> bool:
    return artifact_type in {"image", "svg", "layout_annotation"} or "image" in role


def _source_path(root: Path | None, relative_path: str) -> Path | None:
    if not root or not relative_path:
        return None
    return root / relative_path


def _placeholder(artifact: ArtifactSummary) -> str:
    return (
        f"Artifact: {artifact.artifact_id}\n"
        f"Status: {artifact.status}\n"
        f"Expected path: {artifact.relative_path}\n"
    )

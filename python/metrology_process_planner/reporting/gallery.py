"""Artifact gallery figure generation."""

from __future__ import annotations

from metrology_process_planner.reporting.models import ArtifactSummary, FigureModel

GALLERY_ARTIFACT_TYPES = {
    "image",
    "svg",
    "layout_annotation",
    "process_output",
    "cross_section",
    "overview_map",
}


def gallery_figures(
    artifacts: tuple[ArtifactSummary, ...],
    layout: str = "gallery",
) -> tuple[FigureModel, ...]:
    """Build gallery figures, using placeholders for missing artifacts."""

    figures: list[FigureModel] = []
    for artifact in artifacts:
        if not _is_gallery_artifact(artifact):
            continue
        figures.append(
            FigureModel(
                artifact.artifact_id,
                artifact.label or artifact.artifact_id,
                artifact.artifact_id,
                artifact.relative_path,
                layout=layout,
                notes=_figure_note(artifact),
                placeholder=artifact.placeholder or artifact.status != "present",
            )
        )
    return tuple(figures)


def _is_gallery_artifact(artifact: ArtifactSummary) -> bool:
    return artifact.artifact_type in GALLERY_ARTIFACT_TYPES or "image" in artifact.role


def _placeholder_note(artifact: ArtifactSummary) -> str:
    if artifact.placeholder or artifact.status != "present":
        return f"Placeholder: artifact {artifact.artifact_id} is {artifact.status}."
    return ""


def _figure_note(artifact: ArtifactSummary) -> str:
    placeholder = _placeholder_note(artifact)
    if placeholder:
        return placeholder
    summary = dict(artifact.extensions or {}).get("report_summary")
    if not isinstance(summary, dict):
        return ""
    return str(summary.get("measurement_caption", ""))

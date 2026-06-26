"""Report-facing overview artifact summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.reporting.models import (
    ArtifactSummary,
    FigureModel,
    ReportSection,
)

OVERVIEW_SECTIONS: dict[str, str] = {
    "session_overview": "session_overview",
    "metrology_overview": "metrology_overview",
    "grid_overview": "grid_overview",
    "cad_review_overview": "cad_review_overview",
    "process_planning_overview": "process_planning_overview",
}


@dataclass(frozen=True)
class OverviewReportSummary:
    """Compact overview metadata consumed by report sections and exporters."""

    role: str
    title: str
    labels_requested: int = 0
    labels_placed: int = 0
    labels_omitted: int = 0
    unresolved_collisions: int = 0
    warnings: tuple[str, ...] = ()
    fallback_steps: tuple[str, ...] = ()
    source_items: int = 0

    @property
    def status_label(self) -> str:
        """Return a compact status string for figure notes."""

        if self.unresolved_collisions:
            return "layout warnings"
        if self.labels_omitted:
            return "labels omitted"
        if self.warnings:
            return "warnings"
        return "ready"

    @property
    def body_lines(self) -> tuple[str, ...]:
        """Return report body lines describing placement quality."""

        lines = [
            f"Labels: {self.labels_placed}/{self.labels_requested} placed",
            f"Source targets: {self.source_items}",
            f"Status: {self.status_label}",
        ]
        if self.labels_omitted:
            lines.append(f"Omitted labels: {self.labels_omitted}")
        if self.unresolved_collisions:
            lines.append(f"Unresolved collisions: {self.unresolved_collisions}")
        if self.fallback_steps:
            lines.append(f"Fallbacks: {', '.join(self.fallback_steps)}")
        if self.warnings:
            lines.append(f"Warnings: {', '.join(self.warnings)}")
        return tuple(lines)

    @property
    def figure_notes(self) -> str:
        """Return a compact caption note for image exporters."""

        omitted = f", {self.labels_omitted} omitted" if self.labels_omitted else ""
        collisions = (
            f", {self.unresolved_collisions} unresolved collisions"
            if self.unresolved_collisions
            else ""
        )
        return f"{self.labels_placed}/{self.labels_requested} labels placed{omitted}{collisions}."


def overview_section(section_id: str, artifacts: tuple[ArtifactSummary, ...]) -> ReportSection:
    """Build a report section for one overview artifact role."""

    role = OVERVIEW_SECTIONS[section_id]
    artifact = overview_artifact_for_role(role, artifacts)
    if artifact is None:
        return _missing_section(section_id, role)
    summary = overview_summary_from_artifact(role, artifact)
    figure = FigureModel(
        artifact.artifact_id,
        artifact.label,
        artifact.artifact_id,
        artifact.relative_path,
        notes=summary.figure_notes,
        placeholder=artifact.placeholder,
    )
    return ReportSection(
        section_id,
        role.replace("_", " ").title(),
        body=summary.body_lines,
        figures=(figure,),
    )


def overview_artifact_for_role(
    role: str,
    artifacts: tuple[ArtifactSummary, ...],
) -> ArtifactSummary | None:
    """Return the overview artifact matching a report section role."""

    return next(
        (
            item
            for item in artifacts
            if item.role == role or item.artifact_type == f"{role}_image"
        ),
        None,
    )


def overview_summary_from_artifact(
    role: str,
    artifact: ArtifactSummary,
) -> OverviewReportSummary:
    """Build compact report metadata from an overview artifact summary."""

    data = _mapping(artifact.extensions.get("report_summary"))
    if data:
        return _summary_from_report_extension(role, artifact, data)
    return _summary_from_layout_metadata(role, artifact)


def _summary_from_report_extension(
    role: str,
    artifact: ArtifactSummary,
    data: dict[str, Any],
) -> OverviewReportSummary:
    return OverviewReportSummary(
        role=role,
        title=str(data.get("title") or artifact.label),
        labels_requested=_int(data.get("labels_requested")),
        labels_placed=_int(data.get("labels_placed")),
        labels_omitted=_int(data.get("labels_omitted")),
        unresolved_collisions=_int(data.get("unresolved_collisions")),
        warnings=_strings(data.get("warnings")),
        fallback_steps=_strings(data.get("fallback_steps_used")),
        source_items=_int(data.get("source_items")),
    )


def _summary_from_layout_metadata(
    role: str,
    artifact: ArtifactSummary,
) -> OverviewReportSummary:
    metadata = _mapping(artifact.extensions.get("label_layout_metadata"))
    return OverviewReportSummary(
        role=role,
        title=artifact.label,
        labels_requested=_int(metadata.get("labels_requested")),
        labels_placed=_int(metadata.get("labels_placed")),
        labels_omitted=_int(metadata.get("labels_omitted")),
        unresolved_collisions=_int(metadata.get("unresolved_collisions")),
        warnings=_strings(artifact.extensions.get("warnings")),
        fallback_steps=_strings(metadata.get("fallback_steps_used")),
    )


def _missing_section(section_id: str, role: str) -> ReportSection:
    figure = FigureModel(
        f"missing-{role}",
        role.replace("_", " ").title(),
        "",
        "",
        notes="Overview artifact is missing.",
        placeholder=True,
    )
    return ReportSection(
        section_id,
        role.replace("_", " ").title(),
        body=("Overview artifact is missing.",),
        figures=(figure,),
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _strings(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return ()


def _int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value:
        return int(value)
    return 0

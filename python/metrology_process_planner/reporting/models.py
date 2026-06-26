"""Canonical report document records shared by all exporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ReportMetadata:
    """Identity and provenance for one generated report."""

    report_id: str
    title: str
    template_id: str
    template_name: str
    generated_at: str
    source_session_id: str
    source_session_name: str
    generator_version: str = "0.1.0"
    theme_id: str = "light"


@dataclass(frozen=True)
class CaptureSummary:
    """Renderer-neutral capture summary."""

    capture_id: str
    label: str
    role: str
    status: str
    geometry_kind: str
    measurement_count: int
    artifact_ids: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class MeasurementSummary:
    """Renderer-neutral measurement summary."""

    measurement_id: str
    capture_id: str
    label: str
    measured_length: float
    target: Optional[float] = None
    lower_spec_limit: Optional[float] = None
    upper_spec_limit: Optional[float] = None
    artifact_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArtifactSummary:
    """Renderer-neutral artifact summary."""

    artifact_id: str
    label: str
    artifact_type: str
    role: str
    status: str
    relative_path: str
    owner_type: str
    owner_id: str
    placeholder: bool = False
    extensions: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WarningSummary:
    """Renderer-neutral warning summary."""

    warning_id: str
    severity: str
    message: str
    source: str = ""
    code: str = ""


@dataclass(frozen=True)
class TableModel:
    """Declarative table model consumed by backends."""

    table_id: str
    title: str
    columns: tuple[tuple[str, str], ...]
    rows: tuple[dict[str, Any], ...]
    number: int = 0


@dataclass(frozen=True)
class FigureModel:
    """Declarative figure model consumed by backends."""

    figure_id: str
    title: str
    artifact_id: str
    path: str
    layout: str = "one_image"
    notes: str = ""
    number: int = 0
    placeholder: bool = False


@dataclass(frozen=True)
class ReportSection:
    """One ordered section in a report document."""

    section_id: str
    title: str
    body: tuple[str, ...] = ()
    tables: tuple[TableModel, ...] = ()
    figures: tuple[FigureModel, ...] = ()
    appendix: bool = False


@dataclass(frozen=True)
class ReportDocument:
    """Canonical report document independent of output formats."""

    metadata: ReportMetadata
    project_metadata: dict[str, str]
    session_summary: dict[str, Any]
    captures: tuple[CaptureSummary, ...]
    measurements: tuple[MeasurementSummary, ...]
    artifacts: tuple[ArtifactSummary, ...]
    warnings: tuple[WarningSummary, ...]
    process_context_summary: dict[str, Any]
    sections: tuple[ReportSection, ...]
    appendix_data: dict[str, Any]

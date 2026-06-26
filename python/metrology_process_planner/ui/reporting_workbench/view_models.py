"""View models for the modeless Reporting Workbench."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportingWorkbenchAction:
    """One workbench command button."""

    action_id: str
    label: str
    enabled: bool = True
    disabled_reason: str = ""
    primary_action_id: str = ""


@dataclass(frozen=True)
class SectionPreviewModel:
    """Preview data for one report section."""

    section_id: str
    title: str
    section_type: str
    body: tuple[str, ...] = ()
    table_titles: tuple[str, ...] = ()
    figure_titles: tuple[str, ...] = ()
    readiness: str = "ready"


@dataclass(frozen=True)
class ReportPreviewModel:
    """Preview model for the selected section."""

    selected_section_id: str
    preview_type: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class ReportingWorkbenchModel:
    """Complete modeless Reporting Workbench view model."""

    title: str
    header: tuple[tuple[str, str], ...]
    templates: tuple[tuple[str, str], ...]
    selected_template_id: str
    themes: tuple[tuple[str, str], ...]
    selected_theme_id: str
    primary_action_id: str
    actions: tuple[ReportingWorkbenchAction, ...]
    sections: tuple[SectionPreviewModel, ...]
    preview: ReportPreviewModel
    inspector: tuple[tuple[str, str], ...]
    status: str
    result_fields: tuple[tuple[str, str], ...] = ()

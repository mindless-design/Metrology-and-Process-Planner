"""Mode-aware report section visibility helpers."""

from __future__ import annotations

from metrology_process_planner.domains.modes.mode_registry import ModeRegistry
from metrology_process_planner.domains.session.record import SessionRecord
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware


def effective_report_sections(
    session: SessionRecord,
    sections: tuple[str, ...],
    mode_registry: ModeRegistry | None = None,
) -> tuple[str, ...]:
    """Return sections that belong in the active mode's normal report surface."""

    if mode_is_process_aware(session, mode_registry):
        return sections
    return tuple(section for section in sections if not is_process_report_section(section))


def merged_report_sections(base: tuple[str, ...], additions: tuple[str, ...]) -> tuple[str, ...]:
    """Return base sections with unique additions appended in order."""

    sections = list(base)
    for section_id in additions:
        if section_id not in sections:
            sections.append(section_id)
    return tuple(sections)


def is_process_report_section(section: str) -> bool:
    """Return whether a report section depends on process context or solver output."""

    return section.startswith("process") or section in _PROCESS_REPORT_SECTIONS


_PROCESS_REPORT_SECTIONS = {
    "cross_section",
    "cross_section_gallery",
    "film_thickness_summary",
    "full_stack_compressed",
    "point_stack",
    "process_context",
    "process_outputs",
    "process_report",
    "process_summary",
    "profile_summary",
    "stack_summary",
}

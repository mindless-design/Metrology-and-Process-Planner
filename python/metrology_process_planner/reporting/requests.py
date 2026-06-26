"""Report generation request records and export settings."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PlaceholderPolicy(str, Enum):
    """Missing-artifact behavior for report generation."""

    STRICT = "strict"
    PLACEHOLDER_REQUIRED = "placeholder_required"
    PLACEHOLDER_OPTIONAL = "placeholder_optional"
    OMIT_OPTIONAL = "omit_optional"


@dataclass(frozen=True)
class ReportRequest:
    """Immutable request for one report generation run."""

    session_id: str
    template_id: str
    selected_sections: tuple[str, ...] = ()
    output_formats: tuple[str, ...] = ("pptx", "csv")
    output_dir: Path | None = None
    include_warnings: bool = True
    include_appendix: bool = True
    placeholder_policy: PlaceholderPolicy = PlaceholderPolicy.PLACEHOLDER_REQUIRED
    image_quality: str = "high"
    page_or_slide_size: str = "screen4x3"
    theme_id: str = "light"

    def normalized_sections(self) -> tuple[str, ...]:
        """Return selected sections after warning and appendix flags are applied."""

        sections = list(self.selected_sections)
        if self.include_warnings and "warning_summary" not in sections:
            sections.append("warning_summary")
        if self.include_appendix and "appendix" not in sections:
            sections.append("appendix")
        return tuple(sections)

    def resolved_output_dir(self, default_dir: Path) -> Path:
        """Return the concrete output directory for this request."""

        return self.output_dir if self.output_dir is not None else default_dir

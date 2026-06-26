"""Built-in report template declarations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportTemplate:
    """Declarative report template controlling section selection and layout."""

    template_id: str
    name: str
    required_sections: tuple[str, ...]
    optional_sections: tuple[str, ...] = ()
    supported_mode_families: tuple[str, ...] = ("*",)
    required_artifact_roles: tuple[str, ...] = ()
    export_formats: tuple[str, ...] = ("pptx", "csv", "images.zip")
    page_style: str = "engineering"
    image_layout: str = "gallery"
    table_layout: str = "compact"
    appendix_behavior: str = "include_warnings_and_inventory"

    def ordered_sections(self, requested: tuple[str, ...] = ()) -> tuple[str, ...]:
        """Return required sections followed by allowed requested sections."""

        allowed = set(self.optional_sections)
        extras = tuple(section for section in requested if section in allowed)
        return self.required_sections + tuple(
            section for section in extras if section not in self.required_sections
        )

    def supports_mode(self, mode_id: str) -> bool:
        """Return whether the template supports the session mode family."""

        if "*" in self.supported_mode_families:
            return True
        return any(
            mode_key in self.supported_mode_families
            or any(family in mode_key for family in self.supported_mode_families)
            for mode_key in _mode_support_keys(mode_id)
        )


def _mode_support_keys(mode_id: str) -> tuple[str, ...]:
    aliases = {
        "simple_labeled_capture": "simple_capture",
        "cad_review_capture": "cad_review",
        "cdsem_capture": "cdsem_measurement",
        "cdsem_planning": "cdsem_measurement",
    }
    canonical = aliases.get(mode_id, mode_id)
    return tuple(dict.fromkeys((mode_id, canonical)))


def built_in_report_templates() -> dict[str, ReportTemplate]:
    """Return all built-in report templates keyed by template id."""

    return {
        template.template_id: template
        for template in (
            _engineering_review(),
            _metrology_report(),
            _cad_review_report(),
            _process_review(),
            _fib_package(),
            _process_flow_summary(),
            _debug_artifact_report(),
            _capture_catalog(),
            _measurement_catalog(),
            _executive_summary(),
        )
    }


def _base_optional() -> tuple[str, ...]:
    return ("artifact_gallery", "notes", "appendix", "warning_summary")


def _engineering_review() -> ReportTemplate:
    return ReportTemplate(
        "engineering_review",
        "Engineering Review",
        ("cover_page", "revision_history", "session_summary", "capture_table"),
        _base_optional() + ("measurement_table", "setup_summary"),
    )


def _metrology_report() -> ReportTemplate:
    return ReportTemplate(
        "metrology_report",
        "Metrology Report",
        ("cover_page", "session_summary", "measurement_table", "artifact_gallery"),
        _base_optional() + ("capture_table",),
        ("metrology", "cdsem", "optical", "simple_capture"),
        ("site_image",),
    )


def _cad_review_report() -> ReportTemplate:
    return ReportTemplate(
        "cad_review_report",
        "CAD Review Report",
        ("cover_page", "session_summary", "capture_table", "warning_summary"),
        _base_optional() + ("artifact_gallery",),
        ("cad", "simple_capture"),
    )


def _process_review() -> ReportTemplate:
    return ReportTemplate(
        "process_review",
        "Process Review",
        ("cover_page", "session_summary", "process_context", "artifact_gallery"),
        _base_optional() + ("capture_table", "measurement_table"),
        ("process", "profilometry", "ellipsometry"),
    )


def _fib_package() -> ReportTemplate:
    return ReportTemplate(
        "fib_planning_package",
        "FIB Planning Package",
        ("cover_page", "setup_summary", "capture_table", "artifact_gallery"),
        _base_optional() + ("cross_section_gallery", "measurement_table"),
        ("fib", "process", "metrology", "simple_capture"),
    )


def _process_flow_summary() -> ReportTemplate:
    return ReportTemplate(
        "process_flow_summary",
        "Process Flow Summary",
        ("cover_page", "process_context", "artifact_gallery", "warning_summary"),
        ("appendix", "capture_table"),
        ("process",),
    )


def _debug_artifact_report() -> ReportTemplate:
    return ReportTemplate(
        "debug_artifact_report",
        "Debug Artifact Report",
        ("cover_page", "warning_summary", "appendix"),
        ("artifact_gallery", "capture_table", "measurement_table"),
        ("*",),
        export_formats=("csv", "images.zip"),
    )


def _capture_catalog() -> ReportTemplate:
    return ReportTemplate(
        "capture_catalog",
        "Capture Catalog",
        ("cover_page", "capture_table", "artifact_gallery"),
        _base_optional(),
    )


def _measurement_catalog() -> ReportTemplate:
    return ReportTemplate(
        "measurement_catalog",
        "Measurement Catalog",
        ("cover_page", "measurement_table"),
        _base_optional() + ("capture_table",),
    )


def _executive_summary() -> ReportTemplate:
    return ReportTemplate(
        "executive_summary",
        "Executive Summary",
        ("cover_page", "session_summary", "warning_summary"),
        ("artifact_gallery", "appendix"),
        page_style="summary",
        table_layout="minimal",
        appendix_behavior="warnings_only",
    )

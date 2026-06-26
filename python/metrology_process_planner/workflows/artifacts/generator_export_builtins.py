"""Built-in export artifact generator declarations."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from metrology_process_planner.workflows.artifacts.generator_handlers import (
    rebuild_csv_export,
    write_placeholder_image,
)
from metrology_process_planner.workflows.artifacts.generators import (
    ArtifactGenerator,
    GeneratorRegistration,
)
from metrology_process_planner.workflows.artifacts.report_generator import (
    regenerate_report_artifact,
)


def export_registrations() -> tuple[GeneratorRegistration, ...]:
    """Return built-in export and repair generator declarations."""

    return (
        _registration("csv_export", ("csv_export",), ("session_data",), handler=rebuild_csv_export),
        _registration(
            "powerpoint_export",
            ("powerpoint_deck", "powerpoint_export", "report", "report_manifest"),
            ("report_sections", "source_artifacts"),
            handler=regenerate_report_artifact,
        ),
        _registration(
            "report_export",
            (
                "powerpoint_deck",
                "powerpoint_export",
                "pdf_report",
                "csv_export",
                "image_bundle",
                "report",
                "report_manifest",
            ),
            ("report_sections", "source_artifacts"),
            handler=regenerate_report_artifact,
        ),
        _registration(
            "placeholder_image",
            ("placeholder",),
            ("repair_context",),
            handler=cast(ArtifactGenerator, write_placeholder_image),
        ),
        _registration("debug_trace_export", ("debug_trace",), ("diagnostics",)),
    )


def _registration(
    generator_id: str,
    artifact_types_supported: tuple[str, ...],
    required_inputs: tuple[str, ...] = (),
    handler: ArtifactGenerator | None = None,
) -> GeneratorRegistration:
    registration = GeneratorRegistration(
        generator_id=generator_id,
        artifact_types_supported=artifact_types_supported,
        required_inputs=required_inputs,
        requires_live_layout=False,
        can_run_headless=True,
        output_formats=_output_formats(generator_id),
    )
    return replace(registration, handler=handler) if handler is not None else registration


def _output_formats(generator_id: str) -> tuple[str, ...]:
    if generator_id == "csv_export":
        return ("csv",)
    if generator_id == "powerpoint_export":
        return ("pptx",)
    if generator_id == "report_export":
        return ("pptx", "pdf", "csv", "images.zip")
    if generator_id == "debug_trace_export":
        return ("json", "txt")
    return ("png", "svg")

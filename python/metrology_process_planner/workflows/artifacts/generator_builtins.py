"""Built-in artifact generator declarations."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.workflows.artifacts.generator_export_builtins import (
    export_registrations,
)
from metrology_process_planner.workflows.artifacts.generator_handlers import (
    refresh_measurement_annotation,
    regenerate_overview,
    regenerate_process_output_artifact,
)
from metrology_process_planner.workflows.artifacts.generators import (
    ArtifactGenerator,
    GeneratorRegistration,
)
from metrology_process_planner.workflows.artifacts.layout_crop_generator import (
    LayoutImageExporter,
    layout_crop_generator,
)
from metrology_process_planner.workflows.artifacts.visual_capture_regeneration import (
    regenerate_capture_visual_artifact,
)
from metrology_process_planner.workflows.artifacts.visual_process_generator import (
    regenerate_visual_process_artifact,
)


def built_in_registrations() -> tuple[GeneratorRegistration, ...]:
    """Return built-in generator declarations."""

    return _capture_registrations() + _process_registrations() + export_registrations()


def layout_crop_registration(layout_view: LayoutImageExporter) -> GeneratorRegistration:
    """Return a live-layout crop generator declaration with a concrete handler."""

    return _registration(
        "layout_crop",
        ("captured_site_image", "image"),
        ("source_layout",),
        handler=layout_crop_generator(layout_view),
    )


def _capture_registrations() -> tuple[GeneratorRegistration, ...]:
    return (
        _basic_capture_registrations()
        + _visual_capture_registrations()
        + _overview_registrations()
        + _profile_registrations()
    )


def _basic_capture_registrations() -> tuple[GeneratorRegistration, ...]:
    return (
        _registration("layout_crop", ("captured_site_image", "image"), ("source_layout",)),
        _registration(
            "measurement_annotation",
            ("measurement_detail_image", "measurement_annotation_image"),
            ("parent_capture_image", "measurement_geometry", "annotation_spec"),
            requires_parent_image=True,
            handler=refresh_measurement_annotation,
        ),
    )


def _visual_capture_registrations() -> tuple[GeneratorRegistration, ...]:
    return (
        _registration(
            "visual_capture_polish",
            (
                "site_image_labeled",
                "site_overview_image",
                "site_overview_labeled",
                "site_overview_context",
                "line_annotation_image",
                "point_annotation_image",
                "measurement_annotation_image",
            ),
            ("parent_capture_image", "capture_metadata", "label_policy"),
            handler=regenerate_capture_visual_artifact,
        ),
        _registration(
            "site_with_line_annotation",
            ("annotated_capture_image", "line_annotation_image"),
            ("parent_capture_image", "annotation_spec"),
            requires_parent_image=True,
            handler=regenerate_capture_visual_artifact,
        ),
        _registration(
            "site_with_point_annotation",
            ("annotated_capture_image", "point_annotation_image"),
            ("parent_capture_image", "annotation_spec"),
            requires_parent_image=True,
            handler=regenerate_capture_visual_artifact,
        ),
    )


def _overview_registrations() -> tuple[GeneratorRegistration, ...]:
    return (
        _registration("layout_overview", ("overview_image",), ("source_layout",)),
        _registration(
            "overview_diagram_renderer",
            (
                "overview_image",
                "session_overview_image",
                "metrology_overview_image",
                "grid_overview_image",
            ),
            ("session_data",),
            handler=regenerate_overview,
        ),
        _registration("grid_overview", ("grid_overview",), ("grid_dataset",)),
    )


def _profile_registrations() -> tuple[GeneratorRegistration, ...]:
    return (
        _registration(
            "profile_render",
            ("profile_image",),
            ("measurement_geometry", "recipe_context", "solver_result"),
            requires_recipe=True,
            requires_solver=True,
            handler=regenerate_visual_process_artifact,
        ),
    )


def _process_registrations() -> tuple[GeneratorRegistration, ...]:
    return tuple(
        _process_registration(generator_id, artifact_type, handler)
        for generator_id, artifact_type, handler in (
            ("cross_section_render", "cross_section_image", regenerate_visual_process_artifact),
            ("point_stack_render", "stack_image", regenerate_visual_process_artifact),
            ("process_flow_frame_render", "process_flow_frame", regenerate_visual_process_artifact),
            ("process_output_json", "process_output", regenerate_process_output_artifact),
        )
    )


def _process_registration(
    generator_id: str,
    artifact_type: str,
    handler: ArtifactGenerator,
) -> GeneratorRegistration:
    return _registration(
        generator_id,
        (artifact_type,),
        ("recipe_context", "solver_result"),
        requires_recipe=True,
        requires_solver=True,
        handler=handler,
    )


def _registration(
    generator_id: str,
    artifact_types_supported: tuple[str, ...],
    required_inputs: tuple[str, ...] = (),
    requires_parent_image: bool = False,
    requires_recipe: bool = False,
    requires_solver: bool = False,
    handler: ArtifactGenerator | None = None,
) -> GeneratorRegistration:
    registration = GeneratorRegistration(
        generator_id=generator_id,
        artifact_types_supported=artifact_types_supported,
        required_inputs=required_inputs,
        requires_live_layout=requires_live_layout(generator_id),
        requires_parent_image=requires_parent_image,
        requires_recipe=requires_recipe,
        requires_solver=requires_solver,
        can_run_headless=not requires_live_layout(generator_id),
        output_formats=_output_formats(generator_id),
    )
    return replace(registration, handler=handler) if handler is not None else registration


def requires_live_layout(generator_id: str) -> bool:
    """Return whether a built-in generator needs a live KLayout layout."""

    return generator_id in {"layout_crop", "layout_overview"}


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

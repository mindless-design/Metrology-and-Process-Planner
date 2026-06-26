"""Built-in grid measurement mode definition."""

from __future__ import annotations

from metrology_process_planner.domains.modes.mode_non_process_support import (
    non_process_editor,
    non_process_mode,
)
from metrology_process_planner.domains.modes.mode_output_policies import (
    ArtifactOutputDefinition,
    ArtifactPolicy,
)
from metrology_process_planner.domains.modes.mode_policies import (
    MetadataFieldDefinition,
    MetadataSchema,
)
from metrology_process_planner.domains.modes.mode_registry import ModeDefinition
from metrology_process_planner.domains.session.record import SessionMode

GRID_EDITOR_GROUPS = (
    "dashboard",
    "pending",
    "captures",
    "measurements",
    "grid_datasets",
    "overviews",
    "reports",
    "warnings",
)


def grid_measurement_mode() -> ModeDefinition:
    """Return the built-in recipe-free grid measurement mode."""

    return non_process_mode(
        SessionMode.GRID_MEASUREMENT,
        "Grid Measurement",
        ("site_box", "grid", "measurement"),
        family="grid",
        supports_measurements=True,
        supports_grid_datasets=True,
        metadata=MetadataSchema(
            tuple(
                MetadataFieldDefinition(field_id)
                for field_id in ("label", "notes", "row_count", "column_count", "tags")
            )
        ),
        artifacts=ArtifactPolicy(
            (
                ArtifactOutputDefinition("image", "site_image", required=True),
                ArtifactOutputDefinition("overview", "grid_overview"),
                ArtifactOutputDefinition("measurement_detail", "measurement_detail"),
            )
        ),
        editor=non_process_editor(GRID_EDITOR_GROUPS, ("site_image", "grid_overview")),
        reporting_sections=("grid_dataset",),
    )

"""Process-flow report-only compatibility mode definition."""

from __future__ import annotations

from metrology_process_planner.domains.modes.mode_output_policies import (
    EditorPolicy,
    ProcessPolicy,
    ReportingPolicy,
)
from metrology_process_planner.domains.modes.mode_policies import (
    CaptureSequenceDefinition,
    ModeCapabilities,
)
from metrology_process_planner.domains.modes.mode_registry import ModeDefinition
from metrology_process_planner.domains.session.record import SessionMode


def process_flow_summary_mode() -> ModeDefinition:
    """Return the hidden report-only process-flow compatibility mode."""

    return ModeDefinition(
        SessionMode.PROCESS_FLOW_SUMMARY.value,
        "Process Flow Summary",
        family="process_flow",
        description="Hidden report-only compatibility mode for saved process-flow sessions.",
        visible=False,
        capabilities=ModeCapabilities(
            uses_canvas_objects=False,
            supports_reporting=True,
            supports_artifact_regeneration=True,
        ),
        capture=CaptureSequenceDefinition(primitive_type="site_box"),
        process=ProcessPolicy("forbidden", "none", ""),
        editor=EditorPolicy(("dashboard", "reports", "warnings"), (), (), False),
        reporting=ReportingPolicy(True, ("process_flow_summary",)),
        extensions={"mode_scope": "report_only_compatibility"},
    )

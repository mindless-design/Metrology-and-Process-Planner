"""Extension payload builders for compound capture records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metrology_process_planner.workflows.compound_capture_models import (
    CompoundCaptureRequest,
    InnerFeatureDefinition,
)
from metrology_process_planner.workflows.compound_capture_support import process_outputs_enabled


def process_extension(
    request: CompoundCaptureRequest,
    feature: InnerFeatureDefinition,
    artifact_refs: Mapping[str, str],
    warning_ids: tuple[str, ...],
) -> dict[str, Any]:
    """Return the saved extension payload for one compound capture feature."""

    payload: dict[str, Any] = {
        request.feature_id_field: feature.id,
        "artifact_refs": dict(artifact_refs),
        "warning_ids": list(warning_ids),
    }
    if not process_outputs_enabled(request):
        return payload
    payload.update(
        {
            "process_context_ref": "process_context.active",
            "solver_request": {
                "operation": request.solver_operation,
                "process_window_variant": "target",
                "render_profile": request.render_profile,
            },
            "solver_result_id": None,
        }
    )
    if request.process_output_key == "outputs":
        payload["outputs"] = {"stack_change_windows": [], "step_heights": []}
    else:
        payload[request.process_output_key] = []
    return payload

"""KLayout UI probes for recipe-free session editor surfaces."""

from __future__ import annotations

import textwrap


def non_process_editor_surface_script() -> str:
    """Return a probe that checks live editor regions for recipe/process leakage."""

    return _NON_PROCESS_EDITOR_SURFACE_SCRIPT


_NON_PROCESS_EDITOR_SURFACE_SCRIPT = textwrap.dedent(
    """
        import pya

        from metrology_process_planner.domains.capture.grids import GridDatasetRecord
        from metrology_process_planner.domains.geometry import Box
        from metrology_process_planner.domains.session import (
            CanvasObject,
            CanvasObjectType,
            CanvasWorkflowState,
            CaptureGeometry,
            CaptureRecord,
            SessionMode,
            SessionRecord,
        )
        from metrology_process_planner.domains.session.process_outputs import (
            ProcessContext,
            ProcessOutputRecord,
        )
        from metrology_process_planner.infrastructure.klayout.plugin import (
            _build_klayout_services,
        )
        from metrology_process_planner.workflows.editor.builder import (
            SessionDocumentBuilder,
        )

        FORBIDDEN_ACTIONS = {
            "attach_recipe",
            "detach_recipe",
            "validate_process_context",
            "regenerate_process_output",
            "refresh_recipe_fingerprint",
            "open_recipe_file",
        }
        FORBIDDEN_GROUPS = {"Cross Sections"}
        FORBIDDEN_HEADER_KEYS = {"Process Context"}
        SETUP_MODES = {"optical_metrology", "cdsem_capture", "cdsem_measurement"}

        def _surface_summary(state):
            actions = tuple(state.get("primary_actions", ())) + tuple(state.get("actions", ()))
            navigator = tuple(state.get("navigator", ()))
            return {
                "header_keys": [key for key, _value in state.get("header", ())],
                "header_values": [value for _key, value in state.get("header", ())],
                "action_types": [_action_type(action) for action in actions],
                "action_labels": [action.label for action in actions],
                "navigator_groups": [group_label for group_label, _items in navigator],
                "shown": bool(state.get("shown")),
            }


        def _action_type(action):
            action_type = getattr(action, "action_type", "")
            return getattr(action_type, "value", str(action_type))


        def _assert_recipe_free_surface(mode_id, summary):
            action_types = set(summary["action_types"])
            group_names = set(summary["navigator_groups"])
            header_keys = set(summary["header_keys"])
            leaked_actions = sorted(action_types & FORBIDDEN_ACTIONS)
            leaked_groups = sorted(group_names & FORBIDDEN_GROUPS)
            leaked_headers = sorted(header_keys & FORBIDDEN_HEADER_KEYS)
            if leaked_actions or leaked_groups or leaked_headers:
                raise AssertionError(
                    {
                        "mode": mode_id,
                        "actions": leaked_actions,
                        "groups": leaked_groups,
                        "headers": leaked_headers,
                    }
                )
            if "Dashboard" not in group_names:
                raise AssertionError({"mode": mode_id, "missing": "Dashboard"})
            if mode_id in SETUP_MODES and "Setup" not in group_names:
                raise AssertionError({"mode": mode_id, "missing": "Setup"})
            if mode_id not in SETUP_MODES and "Setup" in group_names:
                raise AssertionError({"mode": mode_id, "unexpected": "Setup"})
            if mode_id == "grid_measurement" and "Grid Datasets" not in group_names:
                raise AssertionError({"mode": mode_id, "missing": "Grid Datasets"})
            if mode_id != "grid_measurement" and "Grid Datasets" in group_names:
                raise AssertionError({"mode": mode_id, "unexpected": "Grid Datasets"})
            if not summary["shown"]:
                raise AssertionError({"mode": mode_id, "missing": "shown window"})


        def _session_for(mode):
            return SessionRecord(
                id="session-" + mode.value,
                name="Recipe Free " + mode.value,
                mode=mode,
                created_at="2026-06-25T00:00:00Z",
                updated_at="2026-06-25T00:00:00Z",
                captures=(_capture(),),
                canvas_objects=(_canvas_object(),),
                grid_datasets=_grid_datasets(mode),
                process_context=ProcessContext(
                    recipe_path="legacy-process-recipe.json",
                    recipe_name="Hidden Legacy Recipe",
                    solver_backend="legacy-solver",
                ),
                process_outputs=(
                    ProcessOutputRecord(
                        "legacy-output",
                        "Hidden Legacy Process Output",
                        "cross_section",
                    ),
                ),
            )


        def _capture():
            return CaptureRecord(
                id="cap-001",
                label="Site 1",
                geometry=CaptureGeometry.box(Box(0, 0, 10, 10)),
                created_at="2026-06-25T00:00:00Z",
            )


        def _canvas_object():
            return CanvasObject(
                "canvas-cap-001",
                "session",
                "cap-001",
                CanvasObjectType.SITE_BOX,
                None,
                CaptureGeometry.box(Box(0, 0, 10, 10)),
                CanvasWorkflowState.SAVED,
            )


        def _grid_datasets(mode):
            if mode is not SessionMode.GRID_MEASUREMENT:
                return ()
            return (GridDatasetRecord("grid-001", "Grid 1", capture_ids=("cap-001",)),)


        services = _build_klayout_services(pya)
        controller = services.session_editor_controller
        builder = SessionDocumentBuilder(mode_registry=controller._mode_registry)
        modes = (
            SessionMode.SIMPLE_CAPTURE,
            SessionMode.SIMPLE_LABELED_CAPTURE,
            SessionMode.FAST_BATCH_CAPTURE,
            SessionMode.CAD_REVIEW,
            SessionMode.CAD_REVIEW_CAPTURE,
            SessionMode.OPTICAL_METROLOGY,
            SessionMode.CDSEM_CAPTURE,
            SessionMode.CDSEM_MEASUREMENT,
            SessionMode.GRID_MEASUREMENT,
        )
        mode_reports = {}

        for mode in modes:
            document = builder.build(_session_for(mode))
            result = controller.open_document(document)
            state = getattr(result.window, "_mpp_state", {})
            summary = _surface_summary(state)
            _assert_recipe_free_surface(mode.value, summary)
            mode_reports[mode.value] = summary

        report.update({"mode_reports": mode_reports})
    """
)

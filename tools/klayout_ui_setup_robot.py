"""KLayout UI probes for recipe-free setup-guide surfaces."""

from __future__ import annotations

import textwrap


def non_process_setup_guide_surface_script() -> str:
    """Return a probe that checks live setup guides for recipe/process leakage."""

    return _NON_PROCESS_SETUP_GUIDE_SURFACE_SCRIPT


_NON_PROCESS_SETUP_GUIDE_SURFACE_SCRIPT = textwrap.dedent(
    """
        import pya

        from metrology_process_planner.domains.session import SessionMode, SessionRecord
        from metrology_process_planner.domains.session.process_outputs import (
            ProcessContext,
            ProcessOutputRecord,
        )
        from metrology_process_planner.infrastructure.klayout.plugin import (
            _build_klayout_services,
        )

        FORBIDDEN_TEXT = (
            "Attach Recipe",
            "Detach Recipe",
            "Validate Process",
            "Regenerate Process",
            "Process Context",
            "Recipe Missing",
            "Stack Image",
            "Profile Image",
            "Solver",
        )


        def _session_for(mode):
            return SessionRecord(
                id="setup-" + mode.value,
                name="Recipe Free Setup " + mode.value,
                mode=mode,
                created_at="2026-06-25T00:00:00Z",
                updated_at="2026-06-25T00:00:00Z",
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


        def _setup_summary(state):
            cards = tuple(state.get("setup_stage_cards", ()))
            actions = tuple(state.get("setup_footer_actions", ()))
            return {
                "card_stage_ids": [card.stage_id for card in cards],
                "card_titles": [card.title for card in cards],
                "primary_action_labels": [card.primary_action_label for card in cards],
                "secondary_action_labels": [
                    label for card in cards for label in card.secondary_action_labels
                ],
                "requirement_labels": {
                    card.stage_id: card.requirement_label for card in cards
                },
                "status": state.get("setup_status", ""),
                "footer_action_labels": [action.label for action in actions],
                "shown": bool(state.get("shown")),
            }


        def _assert_setup_surface(mode_id, summary):
            if not summary["shown"]:
                raise AssertionError({"mode": mode_id, "missing": "shown window"})
            _assert_no_forbidden_text(mode_id, summary)
            _assert_required_stage(mode_id, summary, "optical_alignment")
            if mode_id in {"cdsem_capture", "cdsem_measurement"}:
                _assert_required_stage(mode_id, summary, "sem_alignment")
            if "ready_for_capture" not in summary["card_stage_ids"]:
                raise AssertionError({"mode": mode_id, "missing": "ready_for_capture"})


        def _assert_no_forbidden_text(mode_id, summary):
            labels = _surface_labels(summary)
            leaks = [text for text in FORBIDDEN_TEXT if any(text in label for label in labels)]
            if leaks:
                raise AssertionError({"mode": mode_id, "leaked_text": leaks, "labels": labels})


        def _surface_labels(summary):
            return (
                tuple(summary["card_titles"])
                + tuple(summary["primary_action_labels"])
                + tuple(summary["secondary_action_labels"])
                + tuple(summary["footer_action_labels"])
                + (summary["status"],)
            )


        def _assert_required_stage(mode_id, summary, stage_id):
            if stage_id not in summary["card_stage_ids"]:
                raise AssertionError({"mode": mode_id, "missing": stage_id})
            label = summary["requirement_labels"].get(stage_id)
            if label != "Required":
                raise AssertionError(
                    {"mode": mode_id, "stage": stage_id, "requirement_label": label}
                )


        services = _build_klayout_services(pya)
        controller = services.setup_guide_controller
        modes = (
            SessionMode.OPTICAL_METROLOGY,
            SessionMode.CDSEM_CAPTURE,
            SessionMode.CDSEM_MEASUREMENT,
        )
        mode_reports = {}

        for mode in modes:
            controller.set_active_session(_session_for(mode))
            result = controller.open_current()
            state = getattr(result.window, "_mpp_state", {})
            summary = _setup_summary(state)
            _assert_setup_surface(mode.value, summary)
            mode_reports[mode.value] = summary

        report.update({"mode_reports": mode_reports})
    """
)

# End-to-End Workflow Audit

Last updated: 2026-06-25

This audit records automated evidence where it exists and identifies manual/UI adapter gaps without
inflating them into passes.

| Workflow | Status | Automated/manual | Evidence | Bugs found | Missing contracts / required fixes |
| --- | --- | --- | --- | --- | --- |
| 1. New simple capture session | Pass for command/document core | Automated core, opt-in KLayout release lane | `test_session_document_lifecycle`, `test_session_document_path_commands`, `test_capture_commands`, `test_canvas_interaction_engine`, `test_session_round_trip`, KLayout batch/UI smoke | None in core path | Keep live dialog smoke in release checklist |
| 2. Open existing session | Pass for document/editor core | Automated | `test_session_document_lifecycle`, `test_session_editor_document`, `test_golden_fixtures`, missing artifact fixtures, bind-current-layout command tests | None | Editor without live layout is supported through artifacts |
| 3. Measurement under capture | Pass for core workflow | Automated | `test_measurement_child_workflow`, `test_measurement_validation`, `test_drawing_persistence`, KLayout batch measurement smoke | None | Final prompt styling remains polish |
| 4. Non-process-aware mode | Pass | Automated | `test_non_process_mode_validation`, `test_non_process_mode_hardening`, `test_non_process_dashboard`, `test_non_process_capture_defaults` | None | None found |
| 5. Process-aware compound capture | Pass for core workflow | Automated | `test_compound_capture_workflow`, `test_compound_session_reload`, `test_compound_save_validation`, `test_process_context_workflow` | None | Standalone point and line capture are now covered separately without changing compound child routing |
| 6. Solver to renderer contract | Pass | Automated | `test_solver_contract`, `test_cross_section_rendering_pipeline`, `test_synthetic_solver_regression`, `test_synthetic_render_regression` | None | Continue golden fixture updates through review, not feature work |
| 7. Overview labeling | Pass for geometry/layout contract | Automated, visual QA recommended | `test_overview_diagrams`, `test_overview_label_stress_golden`, overview pipeline fixtures | None | Broader screenshot gallery remains polish |
| 8. Report generation | Pass for service/backends/workbench core | Automated | `test_reporting_pipeline`, `test_reporting_output_quality`, `test_reporting_rendered_quality`, `test_reporting_workbench`, output-adapter and repair tests | None | Final workbench visual polish remains |

## Runtime Baseline

- `python -m pytest`: 669 passed, 19 skipped, 1 warning, 142 subtests passed.
- `python -m tools.quality_gates`: passed.
- Opt-in KLayout GUI automation: 4 tests passed with `MPP_RUN_KLAYOUT_UI_TESTS=1`.
- `python -m tools.release_check --include-klayout`: passed; release check ran unittest discovery, KLayout integration, KLayout process regression, KLayout UI automation, static analysis, compileall, project health, and package build.

## E2E Risk Summary

The document-centered core is coherent. The weak points are not hidden runtime state; they are
known polish/release-evidence gaps: final visual shell polish, broader visual galleries, release-lane
bind/export smoke, and lower-priority artifact handlers that remain explicitly unavailable.

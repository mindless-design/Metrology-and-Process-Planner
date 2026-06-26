# Process And Non-Process Clarity Evaluation

Evaluated: 2026-06-26

## Question

Are process-aware and non-process workflows clearly separated in UI behavior, mode policy, warnings,
available actions, generated artifacts, and reporting paths?

## Summary

The separation is strong at the product-behavior level. Recipe-free modes do not expose process
context, process-output, cross-section, recipe, or solver actions through the editor, setup guide,
diagnostics, reporting, CSV/export paths, or repair state. Process-aware modes retain those actions
and warnings where they are meaningful.

This is one of the better-protected feature areas because the tests cover multiple surfaces, not
just the mode registry.

## Evidence Run

```powershell
python -m unittest `
  tests.test_non_process_dashboard `
  tests.test_non_process_csv_export_modes `
  tests.test_non_process_capture_defaults `
  tests.test_mode_registry_config `
  tests.test_mode_registry `
  tests.test_mode_process_awareness `
  tests.test_non_process_warning_visibility `
  tests.test_non_process_session_editor_header `
  tests.test_non_process_placeholder_artifacts `
  tests.test_non_process_mode_validation_contract `
  tests.test_non_process_mode_validation `
  tests.test_non_process_mode_hardening `
  tests.test_non_process_metadata_fields `
  tests.test_non_process_measurement_modes `
  tests.test_non_process_edit_metadata_action `
  tests.test_non_process_editor_process_leakage `
  tests.test_non_process_editor_legacy_artifacts `
  tests.test_non_process_dispatcher_process_guard `
  tests.test_non_process_dashboard_artifacts `
  tests.test_reporting_non_process_visibility `
  tests.test_ui_state_machines `
  tests.test_diagnostics_dashboard
```

Result: 108 tests passed.

## Findings

### Mode Policy

Status: clear.

Evidence:

- Shared process-awareness predicates match mode policy for built-in non-process modes and
  process-aware modes.
- Non-process mode validation rejects recipe setup stages, process report sections,
  cross-section navigator groups, process previews, and process actions.
- External recipe-free mode definitions can override built-in-looking mode IDs without leaking
  process behavior.

Operator judgment: the mode catalog has a coherent distinction between recipe-free measurement
workflows and process-aware workflows.

### Editor Behavior

Status: clear.

Evidence:

- Recipe-free sessions hide Cross Sections groups, process output items, process dashboard fields,
  process capture metadata, and process actions.
- Forbidden actions such as attach recipe, detach recipe, validate process context, and regenerate
  process output are absent from recipe-free editor states.
- Legacy process records in a recipe-free session are hidden instead of becoming confusing stale UI.

Operator judgment: a non-process operator should not see process-only affordances by accident.

### Setup Guide

Status: clear at the model level.

Evidence:

- Recipe-free setup cards omit recipe/process labels.
- Process-aware setup retains recipe-context stages and validation behavior.
- Setup guide state-machine tests keep recipe context hidden for recipe-free sessions.

Operator judgment: setup behavior follows the selected mode instead of forcing every operator
through process setup.

### Warnings And Diagnostics

Status: clear.

Evidence:

- Process warnings are hidden for recipe-free sessions when they are legacy or irrelevant.
- Diagnostics counts exclude hidden process warnings and artifacts for recipe-free loaded registries.
- Process-aware sessions keep process rows such as recipe context, solver backend, renderer backend,
  and process report readiness.

Operator judgment: diagnostics avoid false process alarms for non-process work while preserving
process visibility where required.

### Artifacts And Repair

Status: clear.

Evidence:

- Process-only repair actions are hidden for non-process artifact tasks.
- Recipe-free dashboards and reports exclude legacy process-output artifacts.
- Placeholder and missing-artifact behavior remains available for non-process artifacts.

Operator judgment: non-process artifact health is still visible, but process-output repair is not
presented as a valid action in recipe-free workflows.

### Reporting And Export

Status: clear.

Evidence:

- Recipe-free reports hide process-context warnings and process-output artifacts.
- Process report sections are omitted when requested against recipe-free documents.
- Readiness checks do not block recipe-free reports on missing process context.

Operator judgment: report output follows the workflow mode instead of mixing process and
non-process narratives.

## Product Risks

1. The separation is behaviorally strong, but terminology still needs manual review in the actual
   Qt surfaces. A hidden action is good; a confusing remaining label would still hurt operators.
2. External mode definitions are flexible. Validation catches many process leaks, but installed
   third-party mode packs should be tested with realistic examples.
3. Process-aware modes must continue to show enough recipe/solver context that hiding logic does
   not become over-broad.

## Conclusion

Feature-driven standing: process-aware and non-process workflows are clearly separated across mode
policy, editor behavior, setup, warnings, diagnostics, artifact repair, and reporting. This goal is
achieved at the product-behavior level.

Recommended follow-up: a manual text audit of the rendered KLayout surfaces to catch any residual
labels that imply process setup inside recipe-free workflows.

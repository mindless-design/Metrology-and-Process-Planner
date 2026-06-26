# Warning And Repair Guidance Evaluation

Evaluated: 2026-06-26

## Question

Do warnings, disabled actions, artifact health states, and repair actions clearly explain what
happened and what the operator should do next?

## Summary

The guidance layer is strong at the behavior-contract level. Warnings are attached to relevant
session items, repair actions are available with payloads, disabled actions expose explicit reasons,
diagnostics actions explain unavailable states, and failed or pending artifacts render as
placeholder previews that tell operators export/reporting can continue.

The remaining risk is copy and visual hierarchy, not the absence of guidance behavior.

## Evidence Run

```powershell
python -m unittest `
  tests.test_warning_repair_actions `
  tests.test_diagnostics_actions `
  tests.test_diagnostics_artifact_repair `
  tests.test_artifact_repair_service `
  tests.test_artifact_repair_lifecycle `
  tests.test_artifact_repair_process_visibility `
  tests.test_ui_artifact_repair_state `
  tests.test_failed_artifact_preview `
  tests.test_editor_render_bridge_repair_preview `
  tests.test_disabled_action_reasons `
  tests.test_reporting_workbench_stale_actions `
  tests.test_report_artifact_repair
```

Result: 47 tests passed.

## Findings

### Warning Actions

Status: clear.

Evidence:

- Process warnings expose attach recipe, validate process context, regenerate process output, open
  recipe file, and ignore-warning actions as appropriate.
- Artifact warnings expose regenerate and relink actions with artifact IDs in the action payload.
- Ignoring a warning updates durable warning status instead of deleting the warning record.
- Process warnings are hidden in recipe-free modes.

Operator judgment: warnings generally point to the next valid action instead of becoming static
messages.

### Disabled Actions

Status: clear.

Evidence:

- Diagnostics actions explain why command trace or session-folder actions are disabled.
- Recipe/editor/report actions preserve disabled reasons and dispatch returns those reasons when
  disabled actions are invoked.
- Setup cards expose disabled reasons such as needing to bind a layout first.

Operator judgment: unavailable actions are not silent. The UI has enough text to explain what
precondition is missing.

### Artifact Health

Status: clear.

Evidence:

- Missing, stale, failed, pending, placeholder, and live-layout-required artifact states are
  represented explicitly.
- Failed and pending artifact previews state the artifact problem, owner, downstream impact, and
  repair suggestion.
- Placeholder previews clarify that CSV export can continue and reports may use placeholders.
- Process-only repair artifacts are hidden in non-process modes.

Operator judgment: artifact problems should be visible without blocking the rest of the workflow.

### Repair Requests

Status: clear.

Evidence:

- Repair routes to registered generators where available.
- Missing dependencies or handler gaps preserve current artifact state and return unavailable
  requests rather than pretending repair succeeded.
- Source-layout requirements are surfaced before live-layout repair is attempted.
- Report artifacts have separate missing/stale repair routing.

Operator judgment: repair actions are actionable when possible and explicit when unavailable.

### Diagnostics

Status: clear.

Evidence:

- Diagnostics can export bundles, copy command traces, open session folders, scan artifacts, export
  artifact health, copy repair queues, validate artifact registries, validate sessions, and validate
  modes.
- Failed diagnostics actions are recorded as diagnostics events.
- Validation results distinguish success, warning, and error outcomes.

Operator judgment: diagnostics provide a support path for understanding and exporting state.

## Product Risks

1. The tests verify action availability and key message text, but not final visual prominence. A
   manual UI pass should confirm that repair suggestions are not buried.
2. Some guidance is necessarily technical, especially around process context, solver, and artifact
   generators. Copy should be reviewed for operator language before external release.
3. Repair queues can grow. The product still needs a high-level prioritization view if many artifacts
   are missing or stale at once.

## Conclusion

Feature-driven standing: warnings, disabled actions, artifact health states, and repair actions
provide clear next-step guidance at the model and command-contract level. Operators should see what
happened, whether work can continue, and which action to take next.

Recommended follow-up: copy and hierarchy review in the live KLayout surfaces, especially for dense
diagnostics and multi-artifact repair cases.

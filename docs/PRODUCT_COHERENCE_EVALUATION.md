# Product Coherence Evaluation

Evaluated: 2026-06-26

## Question

Does the plugin feel like one coherent product rather than a collection of successful subsystems,
with consistent terminology, navigation, action routing, diagnostics, and persistence behavior?

## Summary

The plugin is coherent at the architecture and product-behavior level. The same command catalog,
session document, mode registry, editor document model, diagnostics pipeline, artifact registry,
and modeless window registry are reused across the main surfaces. That gives the product one
spine instead of independent tools stitched together late.

The remaining risk is experience polish: the contracts are unified, but a human still needs to
click through the actual KLayout UI to judge flow, density, and visual hierarchy.

## Evidence Run

```powershell
python -m unittest `
  tests.test_command_registry `
  tests.test_canonical_session_json `
  tests.test_session_round_trip `
  tests.test_session_document_lifecycle `
  tests.test_session_editor_store_dispatcher `
  tests.test_session_editor_command_bridge `
  tests.test_session_editor_shell_controller `
  tests.test_mode_registry `
  tests.test_mode_registry_config `
  tests.test_diagnostics_pipeline `
  tests.test_diagnostics_visibility `
  tests.test_ui_state_machines `
  tests.test_modeless_surface_registry `
  tests.test_window_registry `
  tests.integration.dependency.test_dependency_direction
```

Result: 90 tests passed.

## Findings

### Command Coherence

Status: strong.

Evidence:

- Every `CommandId` has exactly one command spec.
- Menu commands are a stable primary subset with stable KLayout selectors.
- Command specs carry coverage lanes.
- View-model action IDs normalize to typed commands.
- Editor and setup-guide actions route through the shared command router where app ownership is
  required.

Product judgment: actions are not scattered as widget-local behavior. The product has a shared
command vocabulary.

### Persistence Coherence

Status: strong.

Evidence:

- Canonical session JSON writes schema `5.0.0` with top-level sections for session, paths,
  source layout, coordinates, setup, captures, grid datasets, process context, process outputs,
  reports, artifacts, warnings, workflow, extensions, and audit.
- Capture records reference central artifact records instead of storing loose image wrappers.
- Process, grid, report, capture, measurement, and artifact records round-trip through session JSON.
- Unknown top-level fields are preserved on document save.
- Failed saves preserve dirty documents.

Product judgment: `session.json` is the product document, not a side effect of independent features.

### Navigation And Surface Coherence

Status: strong.

Evidence:

- The session editor document indexes dashboard, setup, pending captures, saved captures,
  measurements, process outputs, reports, artifacts, warnings, and canvas objects.
- Modeless surfaces use a shared window registry and reuse windows instead of duplicating state.
- Diagnostics reports open modeless windows.
- UI state machines summarize session, capture, recipe context, pending review, measurement, and
  artifact repair state.

Product judgment: navigation and state flow through shared document/window concepts instead of one
surface per subsystem.

### Diagnostics Coherence

Status: strong.

Evidence:

- Diagnostics pipeline records command, workflow, seam, artifact, warning, and exception state.
- Diagnostics visibility respects mode policy and process-awareness.
- Diagnostics actions export bundles, copy traces, scan artifacts, validate sessions, validate
  modes, and validate artifact registries.

Product judgment: diagnostics are tied into the same product state instead of being an unrelated
debug panel.

### Mode And Workflow Coherence

Status: strong.

Evidence:

- Mode registry/config tests cover built-in and external mode policy.
- Process/non-process UI behavior flows from mode policy.
- Dependency-direction tests keep core document/workflow/reporting/rendering layers independent of
  app, UI, KLayout runtime, and `pya`.

Product judgment: modes shape setup, editor, artifact, process, and reporting behavior through a
shared policy system.

## Product Risks

1. Coherence is proven through contracts and model behavior, not final user perception. The actual
   KLayout UI may still need spacing, naming, and workflow-order adjustments.
2. The current full release gate is not green. Coherence should not be confused with shippability.
3. Because the product is now broad, future feature work can erode coherence unless command,
   document, mode, artifact, and diagnostics seams remain mandatory.
4. The docs now contain several evaluation artifacts. They should be curated into a single release
   readiness narrative before handoff.

## Conclusion

Feature-driven standing: the plugin behaves like one coherent product at the system-contract level.
Session persistence, command routing, modeless surfaces, diagnostics, mode policy, artifact health,
and reporting share common state and vocabulary.

Recommended follow-up: perform one end-to-end manual KLayout operator walkthrough and record UI
friction as product polish issues rather than architecture gaps.

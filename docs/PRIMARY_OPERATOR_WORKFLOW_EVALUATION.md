# Primary Operator Workflow Evaluation

Evaluated: 2026-06-26

## Question

Can a real operator complete the primary Metrology and Process Planner workflow in KLayout without
knowing implementation details?

Primary workflow:

1. Create or open a session.
2. Bind the active KLayout layout.
3. Complete setup or attach recipe/process context.
4. Capture geometry.
5. Review and save captures or measurements.
6. Generate or repair artifacts.
7. Inspect diagnostics.
8. Export/report results.

## Summary

The operator workflow is present end to end at the product-behavior level. The plugin has enough
session, layout-binding, setup, capture, process-output, artifact-repair, diagnostics, and reporting
behavior for an operator to move through the intended loop without interacting with implementation
modules directly.

The strongest evidence is not the full release gate. The current release gate is blocked by
maintainability, formatting, one stale CSV golden, and an environment-level Cairo/interrogate issue.
Those are real release blockers, but they do not invalidate the feature-level conclusion here.

## Evidence Run

Focused product workflow slice:

```powershell
python -m unittest `
  tests.test_session_document_lifecycle `
  tests.test_session_lifecycle_commands `
  tests.test_session_layout_binding_commands `
  tests.test_setup_guide_recipe_commands `
  tests.test_session_editor_process_command_bridge `
  tests.test_standalone_point_capture `
  tests.test_standalone_line_capture `
  tests.test_process_output_loop `
  tests.test_artifact_repair_service `
  tests.test_reporting_workbench `
  tests.test_diagnostics_dashboard
```

Result: 44 tests passed.

KLayout operator-boundary slice:

```powershell
$env:KLAYOUT_EXE='C:\Users\edmun\AppData\Roaming\KLayout\klayout_app.exe'
$env:MPP_RUN_KLAYOUT_TESTS='1'
$env:MPP_RUN_KLAYOUT_UI_TESTS='1'
python -m unittest `
  tests.test_klayout_integration `
  tests.test_klayout_process_regression `
  tests.test_klayout_ui_automation
```

Result: 21 tests passed.

## Workflow Findings

### 1. Session Start And Recovery

Status: supported.

Evidence:

- New/open/save/save-as/recent behavior is backed by `SessionDocument`, `SessionStore`,
  `ActiveSessionContext`, and command adapters.
- The editor has a no-active-session start state with actions for New Session, Open Existing
  Session JSON, and Open Recent.
- Dirty close and pending-capture close are blocked with structured operator guidance instead of
  silently discarding work.

Operator judgment: a user can enter and leave the session workflow through product commands rather
than developer-only scripts.

### 2. Layout Binding

Status: supported.

Evidence:

- `Bind Current Layout to Session` updates canonical `SourceLayoutContext`, persists it, restores
  durable overlays, and warns on layout mismatch.
- KLayout tests verify menu registration, current-view availability, and layout/capture boundary
  behavior.

Operator judgment: a session can be connected to the live KLayout context, and mismatches are
visible rather than hidden.

### 3. Setup And Recipe Context

Status: supported, with polish remaining.

Evidence:

- Setup guide actions route through the shared command router.
- Recipe attach uses a host-injected recipe path picker.
- Process-context commands attach, detach, validate, and preserve selected recipe paths through
  editor actions.
- Non-process setup and editor surfaces hide recipe/process controls in KLayout UI automation.

Operator judgment: process-aware setup is usable without editing JSON manually. The remaining risk
is presentation clarity, not missing backend behavior.

### 4. Capture And Review

Status: supported.

Evidence:

- KLayout UI automation verifies box capture, measurement capture, standalone line capture, and
  standalone point capture surface contracts.
- Pure workflow tests verify standalone point and line captures save into canonical capture records
  with durable canvas objects.
- Session lifecycle commands block closing while pending capture review is unresolved.

Operator judgment: core geometry capture is available through the intended gesture/review model.

### 5. Process Output Generation

Status: supported for workflow claims, not calibrated-physics claims.

Evidence:

- Process regeneration generates ellipsometry point-stack outputs, profilometry line-profile
  outputs, FIB full-stack compressed outputs, and process-flow frame metadata.
- Missing recipe paths produce warnings and placeholder artifacts rather than blocking capture save.
- KLayout process regression verifies synthetic GDS loading, mask extraction, solver summaries,
  render scene summaries, and Qt rasterization.

Operator judgment: process-aware outputs can be generated and reviewed. The solver is still bounded
by the documented accuracy envelope and should not be presented as calibrated fabrication physics.

### 6. Artifact Repair

Status: supported.

Evidence:

- Missing, stale, dependency-blocked, and handler-unavailable artifacts produce explicit repair
  requests or unavailable states.
- Repair routes to registered generators when available.
- Missing source-layout requirements are surfaced before a live layout repair is attempted.

Operator judgment: artifact problems are visible and actionable enough for product use.

### 7. Diagnostics

Status: supported.

Evidence:

- Diagnostics dashboard exposes session path, dirty state, loaded mode definition, workflow state,
  report readiness, recent commands, actions, and process rows for process-aware sessions.
- Blocked commands are recorded as diagnostics events.
- KLayout modeless command-surface tests open diagnostics successfully and verify diagnostic events.

Operator judgment: an operator or support user has a product surface for understanding state and
next actions.

### 8. Reporting And Export

Status: supported for PowerPoint/report-workbench flow; broader export polish remains.

Evidence:

- Session editor can open the Reporting Workbench.
- Workbench exports PowerPoint, handles missing images with placeholders, exposes open/regenerate
  report actions, and refreshes previews when template/section selection changes.
- Report artifacts can be regenerated through repair metadata.

Operator judgment: the report loop is usable enough for review and sharing, but should still receive
visual and UX polish before calling it final.

## Product Risks

1. The editor shell is functional but still described as minimal/generic. A real operator can use
   it, but the experience may feel like a model-view surface rather than a finished product UI.
2. Manual dialog smoke remains a release checklist item for layout rebinding and picker flows.
   Automated KLayout coverage is strong, but it does not fully replace a human click-through pass.
3. Release health is currently not green. The failed release check is mostly guardrail/golden/tool
   configuration work, but it must be resolved before shipping.
4. Reporting and visual outputs are usable, but broader gallery review and visual polish remain
   worthwhile before external presentation.
5. The solver output is workflow-ready with synthetic regression coverage, not a calibrated physics
   simulator. The UI and reports should keep that distinction visible.

## Conclusion

Feature-driven standing: the primary operator workflow is implemented and verified across both
pure workflow services and live KLayout integration boundaries. The product is no longer missing
the core loop.

Release-driven standing: not ready to ship until quality-gate violations, stale CSV golden output,
ruff formatting, xenon complexity, and the Cairo/interrogate environment issue are resolved.

Recommended next goal: evaluate whether the modeless surfaces are understandable and polished enough
for operators, because the workflow exists but the quality of the product experience is now the main
feature risk.

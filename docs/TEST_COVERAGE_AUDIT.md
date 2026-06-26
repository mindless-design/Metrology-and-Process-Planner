# Test Coverage Audit

Last updated: 2026-06-25

## Coverage Summary

The test suite is broad. It includes unit tests for command registry, session JSON, editor models, setup guide, captures, measurements, compound workflows, modes, artifacts, diagnostics, process context, solver, rendering, overview diagrams, reporting, release checks, quality gates, dependency direction, golden fixtures, and opt-in KLayout lanes.

Existing evidence in repository docs reports a passing release lane including unit tests, quality gates, import direction checks, KLayout batch/process/UI lanes, compileall, static analysis, project health, and package build. This audit did not rerun the full release lane; see verification notes in the final task response.

## Feature Coverage

| Area | Coverage | Evidence | Gaps |
| --- | --- | --- | --- |
| session document lifecycle | tested | session lifecycle/document/store/round-trip tests | UI file picker paths |
| mode registry and validation | tested | mode registry/validation/non-process tests | installed external mode discovery |
| command registry/menu metadata | tested | command registry/UI layer tests, KLayout UI automation | path command adapters |
| setup guide | tested | state machine, required stages, commands, badges | production Qt shell visual behavior |
| box capture | tested | canvas interaction, capture commands, KLayout smokes | live overlay rebinding |
| line/measurement workflow | tested | measurement workflow, validation, completion, KLayout line smoke | final prompt UI |
| point capture | tested | standalone point, point boundary, ellipsometry compound point | broaden live visual coverage |
| compound captures | tested | compound workflow/save/reload/routing/metadata | richer process artifacts |
| persistent overlays | tested | canvas overlays/selection/reload | real view binding |
| editor view models/shell | tested | shell controller, navigator, document, store dispatcher | polished Qt shell |
| artifacts/repair | tested | artifact lifecycle/repair/scanner/UI repair state | generator handlers |
| metadata CSV export | tested | capture annotation export, CSV export artifacts | copy-coordinate UI |
| process context/recipe | tested | process context validation/workflow/dashboard | recipe file picker/open path |
| solver | tested | solver contract, hybrid solver, golden regression | physical accuracy limits remain documented |
| renderer | tested | cross-section rendering, synthetic render regression | visual regression on dense real cases |
| overview labeling | tested | overview diagrams | manual visual QA for dense layouts |
| reporting | tested | readiness, pipeline, output quality, workbench, PPTX/PDF | destination picker UX |
| diagnostics | tested | diagnostics pipeline/actions/visibility | final dashboard UI |
| KLayout smoke | tested opt-in | KLayout integration/UI automation tests | broader GUI gestures |
| visual regression | partially tested | synthetic render regression and report rendered quality | screenshots for final Qt UI |
| end-to-end workflows | partially tested | E2E audit, workflow slices | complete operator path from menu/file picker |

## Manual-Only or Missing Tests

- Actual Qt/KLayout file-picker driven New/Open/Open Recent/Save As.
- `Bind Current Layout to Session` against a real live layout/view.
- Delayed overlay restoration after closing/reopening a session and binding a compatible layout.
- Installed external JSON mode folder discovery.
- Recipe open/select file picker workflows.
- Dense real-layout visual regression for overview labels and final Qt shells.
- Concrete generator handlers as they are added.

## Recommended Test Priorities

1. Add UI-adapter tests for all currently unavailable document lifecycle commands.
2. Add live KLayout binding and overlay restore tests.
3. Add installed-mode discovery/configuration tests.
4. Add visual regression screenshots for production Qt editor/setup/diagnostics/reporting shells.
5. Keep `python -m tools.release_check --include-klayout` as the high-confidence gate when shippability matters.

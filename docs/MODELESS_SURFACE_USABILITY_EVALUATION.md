# Modeless Surface Usability Evaluation

Evaluated: 2026-06-26

## Question

Are the session editor, setup guide, recipe editor, diagnostics panel, and reporting workbench
understandable as product surfaces rather than just technically wired views?

## Summary

The modeless surfaces are product-shaped. They expose operator labels, visible actions, disabled
reasons, reusable windows, state summaries, previews, badges, and callbacks through shared view
models instead of requiring knowledge of internal services.

They are not yet polished UI in the visual-design sense. The evidence proves understandable
surface contracts and workflow affordances, not final layout quality or manual operator delight.

## Evidence Run

```powershell
python -m unittest `
  tests.test_ui_layer_redesign `
  tests.test_modeless_surface_registry `
  tests.test_window_registry `
  tests.test_setup_guide_card_models `
  tests.test_setup_guide_badges `
  tests.test_recipe_editor_header `
  tests.test_recipe_editor_cards `
  tests.test_recipe_editor_step_cards `
  tests.test_diagnostics_dashboard `
  tests.test_reporting_workbench
```

Result: 45 tests passed.

## Surface Findings

### Session Editor

Status: understandable as the main product shell.

Evidence:

- Menu entries use operator-facing command names such as Session Editor, Open Session, New Session,
  Advanced Diagnostics, and Reporting Workbench.
- Header actions route through product commands and expose save, setup, process, export, report,
  output-folder, and close affordances.
- Preview widgets use artifact labels, statuses, placeholder text, and repair hints.

Remaining risk: the editor shell is still generic. It is a coherent modeless surface, but a manual
operator pass should check scanability, grouping, and whether primary actions feel obvious without
reading docs.

### Setup Guide

Status: understandable as a workflow surface.

Evidence:

- Setup stage cards expose status labels, status tones, requirement badges, artifact badges,
  warning counts, disabled reasons, and active-stage state.
- Setup actions route through the command router, and the shared registry reuses the window instead
  of opening duplicates.
- Non-process setup guides hide recipe/process labels.

Remaining risk: card models are strong; final Qt card styling and density still need visual review.

### Recipe Editor

Status: understandable for recipe state and editing.

Evidence:

- The header exposes recipe path, dirty state, validation state, and attachment state.
- Recipe-specific actions are disabled with concrete reasons when no recipe is loaded, when a recipe
  is unsaved, or when it must be saved before attachment.
- Step cards expose action parity for duplicate, delete, move, enable/disable, and preview-through-
  step behavior.

Remaining risk: the recipe editor has the right affordances, but complex recipe editing should get
  a separate real-user flow pass for discoverability and error recovery.

### Diagnostics Panel

Status: understandable as a support/operator state panel.

Evidence:

- Diagnostics reports active session, dirty state, loaded mode definition, workflow state, report
  readiness, recent commands, open windows, warning codes, and artifact-repair queue status.
- It distinguishes process-aware and recipe-free sessions when showing process/report sections.
- It exposes diagnostic actions such as exporting bundles and validation actions with disabled
  reasons where needed.

Remaining risk: diagnostics are information-rich. The next usability question is hierarchy: what is
  first-level operator guidance versus support/debug detail?

### Reporting Workbench

Status: understandable enough for report generation.

Evidence:

- Opening from the session editor creates a shown modeless Report Workbench.
- The workbench exposes selected templates, themes, preview section selection, result fields, and
  open/regenerate actions after export.
- Missing image artifacts produce an explicit Export with Placeholders primary action.

Remaining risk: reporting is functionally clear, but the generated output and workbench layout still
  need broader visual review before external presentation.

## Conclusion

Feature-driven standing: the modeless surfaces are not just backend endpoints. They expose enough
state, labels, actions, disabled reasons, and previews for an operator to understand what each
surface is for and what to do next.

Main remaining risk: visual and interaction polish. The product contracts are in place; the next
step is manual click-through and visual QA of the actual KLayout-rendered surfaces.

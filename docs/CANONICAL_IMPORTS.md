# Canonical Imports

Last updated: 2026-06-25.

Use canonical module paths for internal imports. Package-root imports are tolerated only for
documented stable public APIs and tests that intentionally exercise those APIs.

## Core Session And Persistence

| Concept | Canonical import location |
| --- | --- |
| `SessionRecord` | `metrology_process_planner.domains.session.record` |
| `SessionMode`, `SessionModeId` | `metrology_process_planner.domains.session.record` |
| `SessionDocument` | `metrology_process_planner.workflows.editor.document` |
| session JSON load/save | `metrology_process_planner.persistence.json_store` |
| session paths | `metrology_process_planner.persistence.paths` |
| schema validation | `metrology_process_planner.persistence.schema` |
| recent/session repair helpers | `metrology_process_planner.persistence.repair` and `metrology_process_planner.persistence.session_repair` |

## Domain Records

| Concept | Canonical import location |
| --- | --- |
| `CaptureGeometry`, `GeometryKind` | `metrology_process_planner.domains.capture.capture_geometry` |
| `CaptureRecord` | `metrology_process_planner.domains.capture.captures` |
| `CanvasObject`, `CanvasObjectType`, `PendingCapture` | `metrology_process_planner.domains.capture.canvas` |
| `GridDatasetRecord` | `metrology_process_planner.domains.capture.grids` |
| `MeasurementRecord`, `MeasurementStatus` | `metrology_process_planner.domains.measurement.records` |
| `ArtifactRecord`, `ArtifactStatus`, `ArtifactPathMode` | `metrology_process_planner.domains.artifacts.artifact_registry` |
| `ArtifactFileMetadata`, `ArtifactOwnerRef`, `ArtifactDependencyRef` | `metrology_process_planner.domains.artifacts.artifact_refs_metadata` |
| `ArtifactRepairMetadata` | `metrology_process_planner.domains.artifacts.artifact_repair_metadata` |
| artifact visibility helpers | `metrology_process_planner.domains.artifacts.artifact_visibility` |
| `WarningRecord` | `metrology_process_planner.domains.warnings.warnings` |
| warning visibility helpers | `metrology_process_planner.domains.warnings.warning_visibility` |

## Modes And Workflows

| Concept | Canonical import location |
| --- | --- |
| `ModeDefinition`, `ModeRegistry`, `built_in_mode_registry` | `metrology_process_planner.domains.modes.mode_registry` |
| mode loading | `metrology_process_planner.domains.modes.mode_loader` |
| mode validation | `metrology_process_planner.domains.modes.mode_validation` |
| mode execution planning | `metrology_process_planner.domains.modes.mode_execution` |
| mode capture/setup/measurement policies | `metrology_process_planner.domains.modes.mode_policies` |
| mode output/editor/reporting policies | `metrology_process_planner.domains.modes.mode_output_policies` |
| capture workflow | `metrology_process_planner.workflows.canvas_interaction`, `metrology_process_planner.workflows.capture_replacement`, or the narrower capture workflow module that owns the action |
| measurement workflow | `metrology_process_planner.workflows.measurement_workflow` |
| setup guide workflow | `metrology_process_planner.workflows.setup_guide_state` and stage-specific setup modules |
| artifact repair workflow | `metrology_process_planner.workflows.artifacts.repair` |
| editor document/view models | `metrology_process_planner.workflows.editor.document` and `metrology_process_planner.workflows.editor.view_models` |

## Process, Solver, Rendering, Reporting

| Concept | Canonical import location |
| --- | --- |
| `Material`, `LayerReference` | `metrology_process_planner.domains.process.materials` |
| `ProcessRecipe` | `metrology_process_planner.domains.process.recipe` |
| `ProcessStep`, `ProcessStepKind`, `ThicknessSpec` | `metrology_process_planner.domains.process.steps` |
| recipe validation | `metrology_process_planner.domains.process.validation` |
| `HybridCrossSectionSolver` | `metrology_process_planner.solver.hybrid_solver` |
| solver inputs/results/profiles | `metrology_process_planner.solver.solver_models` |
| solver geometry models | `metrology_process_planner.solver.geometry_models` |
| solver operations | `metrology_process_planner.solver.operations` and operation-specific solver modules |
| render projection validation | `metrology_process_planner.domains.process.render_contract` |
| render specs/profiles | `metrology_process_planner.rendering.specs` |
| cross-section rendering | `metrology_process_planner.rendering.cross_section.pipeline` |
| overview rendering | `metrology_process_planner.rendering.overview.renderer` |
| report document/building | `metrology_process_planner.reporting.builder` |
| report readiness | `metrology_process_planner.reporting.readiness` |
| report exporters | format-specific reporting modules such as `metrology_process_planner.reporting.csv_backend`, `metrology_process_planner.reporting.pdf_backend`, `metrology_process_planner.reporting.pptx_backend`, and `metrology_process_planner.reporting.image_backend` |

## App, UI, Infrastructure, Diagnostics

| Concept | Canonical import location |
| --- | --- |
| command IDs and catalog | `metrology_process_planner.app.commands` and `metrology_process_planner.app.command_catalog` |
| active session context | `metrology_process_planner.app.active_session` |
| window registry | `metrology_process_planner.app.window_registry` |
| session editor shell | `metrology_process_planner.ui.session_editor.shell` |
| setup guide UI | `metrology_process_planner.ui.setup_guide` |
| recipe editor UI | `metrology_process_planner.ui.recipe_editor` |
| capture UI tools | `metrology_process_planner.ui.capture.tools` |
| KLayout adapters | `metrology_process_planner.infrastructure.klayout` and narrower adapter modules |
| Qt helpers | `metrology_process_planner.infrastructure.qt` or relevant `ui` module |
| diagnostic events/sinks | `metrology_process_planner.diagnostics.diagnostics` and `metrology_process_planner.diagnostics.diagnostics_sinks` |
| diagnostics snapshots | `metrology_process_planner.diagnostics.diagnostics_snapshots` |
| diagnostics project bundle | `metrology_process_planner.diagnostics.diagnostics_project` |
| trace context | `metrology_process_planner.diagnostics.trace_context` |

## Forbidden Internal Paths

Do not import from deleted shim paths such as:

- `metrology_process_planner.domains.measurements`
- `metrology_process_planner.domains.session.artifact_*`
- `metrology_process_planner.domains.session.capture_*`
- `metrology_process_planner.domains.session.mode_*`
- `metrology_process_planner.domains.session.warning*`
- `metrology_process_planner.domains.process.<solver module>`
- `metrology_process_planner.infrastructure.diagnostics*`
- `metrology_process_planner.infrastructure.trace_context`

Run `python -m tools.audit_imports` before closing architecture work.

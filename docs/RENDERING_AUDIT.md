# Rendering Audit

Last updated: 2026-06-25

## Pipeline

The renderer architecture is implemented as a contract pipeline:

`SolverResult -> RenderIntent -> RenderProjection/scene planning -> CrossSectionSceneModel -> renderer backend -> ArtifactRecord`.

The solver domain owns `SolverInput`, `SolverResult`, `ProcessFrame`, diagnostics, and render projection validation. Rendering owns profiles, intents, scene models, SVG export, cross-section rendering, and overview diagrams. The solver does not need to know renderer private internals.

## Render Modes

| Render mode | Status | Evidence | Gaps |
| --- | --- | --- | --- |
| proportional_physical | implemented | `physical_cross_section` profile and tests | visual QA on real recipes still useful |
| illustrative_process | implemented | illustrative process profile, compression/thin-layer policies | concrete artifact generator breadth |
| profilometry_surface | implemented | surface profile render mode and golden tests | richer profile image output |
| fib_full_stack_compressed | implemented | FIB render profile and tests | no `fib_cut_planner` mode |
| process_flow_frame | implemented | process-flow frame profile and tests | process-flow product UX thin |
| point_stack_schematic | implemented | point stack profile and ellipsometry policy | stack table/image generator breadth |

## Cross-Section Capabilities

| Capability | Status | Notes |
| --- | --- | --- |
| feature filtering | implemented | `FeatureFilter` and render intent policies |
| full-stack compression | implemented | compression metadata and break marks |
| thin-layer exaggeration | implemented | min visual thickness and warnings |
| conformal coating visualization | implemented | solver emits conformal diagnostics; renderer handles thin layers |
| surface/topography filtering | implemented | profilometry surface profile |
| material labels | implemented | label candidates and placement |
| process-step labels | implemented | profiles can show step labels |
| leaders/callouts | implemented | cross-section label leaders/callouts and overview leaders |
| collision avoidance | partially_implemented | collision warnings exist; manual dense QA needed |
| compression metadata | implemented | scene metadata and render result metadata |
| render warnings | implemented | scene warnings and artifact warnings |
| artifact integration | mostly_implemented | records, bridges, and visual process repair generators exist; dense visual QA remains |

## Overview Labeling

Overview labeling has request, target extraction, content builder, outside-edge layout, leader routing, collision warnings, SVG renderer, artifact writer, and tests. It supports session/capture/measurement/process-oriented overviews at the core-contract level. Dense real-layout output should be visually reviewed before being called production-polished.

## Artifact Types

Rendering-related artifact types are supported as registry records or generator declarations: `overview_image`, `profile_image`, `cross_section_image`, `full_stack_compressed_image`, `process_flow_frame`, `stack_image`, `point_annotation`, `line_annotation`, `measurement_detail_image`, and placeholders. Profile, cross-section, full-stack, stack, and process-flow visual process artifacts now repair through solver/render SVG generation.

## Recommended Actions

1. Add dense real-layout visual QA for cross-section, profile, point stack, and overview images.
2. Keep solver/render accuracy envelopes current through `docs/SOLVER_ACCURACY_ENVELOPE.md`.
3. Add product mode support for FIB if FIB full-stack rendering is meant to be user-facing.
4. Keep render projection validation in the release lane.

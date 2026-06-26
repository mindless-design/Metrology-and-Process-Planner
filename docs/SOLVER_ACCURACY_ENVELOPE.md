# Solver Accuracy Envelope

Last updated: 2026-06-25

## Purpose

The current `HybridCrossSectionSolver` is a sampled 2D process-visualization solver. It is stable enough for document workflow, artifact generation, render projections, process-flow summaries, and regression fixtures.

It is not a calibrated semiconductor process simulator.

## Contract

Every executable synthetic recipe fixture must declare:

- `metadata.fixture_target`: the behavior the fixture protects.
- `metadata.accuracy_envelope.model`: the solver model family.
- `metadata.accuracy_envelope.claim`: the confidence level.
- `metadata.accuracy_envelope.covers`: intentionally protected behaviors.
- `metadata.accuracy_envelope.excludes`: physical effects that are out of scope.

`tests/test_synthetic_solver_regression.py` enforces this metadata for executable solver fixtures.

## Current Claims

| Fixture family | Claim level | Protected behavior |
| --- | --- | --- |
| simple stack | contract_fixture | material ordering, blanket deposition, patterned deposition |
| patterned deposition | qualitative_cross_section | mask interval deposition and simple topography following |
| directional etch | qualitative_cross_section | vertical removal, stop-material preservation, depth diagnostics |
| isotropic undercut | qualitative_cross_section | lateral attack parameter and undercut diagnostics |
| tapered etch | qualitative_cross_section | sidewall metadata, top/bottom CD bias, taper diagnostics |
| conformal liner | qualitative_cross_section | coverage metadata, thin-layer visibility, pinch-off diagnostics |
| CMP planarization | qualitative_cross_section | target-plane planarization, stop layers, dishing diagnostic |
| profilometry surface | qualitative_profile | top-surface extraction and buried-feature exclusion |
| FIB full stack | visual_stack_fixture | material ordering, compression, thin-layer visibility |
| process flow | workflow_contract_fixture | frame ordering, changed-frame detection, process-window labels |

## Explicit Non-Claims

The solver does not currently claim calibrated etch/deposition rates, lithography calibration, process chemistry, microloading, ARDE, true conformal surface evolution, void nucleation, CMP rate modeling, profilometer instrument response, FIB milling physics, 3D corner rounding, or volumetric process simulation.

## Expansion Rule

Future P3.4 solver work should add physics only with a fixture recipe, an updated accuracy envelope, a golden solver summary, a render projection or scene regression when visual output changes, and diagnostics that disclose approximations.

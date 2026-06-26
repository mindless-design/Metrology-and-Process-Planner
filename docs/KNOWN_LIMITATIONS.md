# Known Limitations

Last updated: 2026-06-25

## P0 Limitations

| Limitation | Status | Impact | Required fix |
| --- | --- | --- | --- |
| Top-level New/Open/Open Recent/Save As menu commands cannot collect paths/mode/destinations | resolved | None in command-path coverage | Keep live KLayout dialog smoke in release lane |
| Bind Current Layout to Session release smoke | resolved in command-path coverage | None in unit/boundary coverage | Keep live KLayout bind smoke in release lane |

## Product Limitations

| Area | Limitation | Status |
| --- | --- | --- |
| UI shell | Editor/setup/diagnostics/reporting surfaces are command-routed and testable, but final visual polish remains | polish_gap |
| Mode catalog | `fib_cut_planner` is intentionally descoped from the visible catalog until implemented as a complete mode | documented |
| Mode catalog | `process_flow_summary` exists as report-only/load-compatible mode but is hidden from new-session picker | documented |
| Mode catalog | `process_aware_metrology` exists as internal compatibility mode and is hidden from new-session picker | documented |
| Legacy aliases | `cdsem_capture` and `cdsem_planning` remain load-compatible but are hidden; `cdsem_measurement` is the visible operator mode | documented |
| Capture | Standalone point and line captures persist and are covered by KLayout boundary/UI probes; visual styling and richer point/line imagery remain polish | polish_gap |
| Artifacts | Registry and repair metadata are strong, with concrete handlers for CSV, placeholders, annotations, overviews, process-output JSON, PowerPoint report outputs, injected live layout crop repair, and visual process SVG repair; lower-priority handlers remain explicitly unavailable | scope_limited |
| Reporting | Headless service, workbench export, generated PowerPoint repair, and output adapters work; production shell polish and broader output-format repair remain | polish_gap |
| Recipe flow | Recipe open/save-as/setup-attach path selection is wired through host adapters; broader recipe editor visual polish remains | polish_gap |
| Overview rendering | Dense real-layout label routing has golden summary coverage; broader screenshot galleries remain polish | polish_gap |
| KLayout automation | Batch and UI smokes cover menus, modeless surfaces, process/capture probes, and GUI capture contracts; full OS-level mouse automation remains out of scope | release_lane |
| KLayout automation | Live bind-current-layout smoke is opt-in and should be run before release packaging | release_lane |
| External modes | Configured folders load into the app registry and diagnostics, and visible registered custom IDs can be selected, persisted, and projected into generic editor view models; product behavior is limited to declarative policies supported by shared workflows | scope_limited |

## Technical Limitations

- The process solver is an approximate sampled geometry solver, not a replacement for full process simulation; target-exhausted and non-target-blocked etches are surfaced as diagnostics rather than calibrated process predictions.
- Some render outputs are contract-complete but still need broader visual galleries beyond the dense overview regression.
- Diagnostics inspect service state, recent events, and grouped dashboard rows; live visual polish remains.
- Some platform actions return typed handoffs rather than invoking OS/KLayout UI directly from workflow code.
- Recent sessions are currently an in-memory registry unless a caller persists them.

## Not Limitations

- Session JSON itself is not missing; it is canonical and schema-validated.
- Captures and measurements are not UI-only; they have durable records.
- Overlays are not canonical state; they are durable proxies derived from session records.
- Reports do not require live UI state in the headless service path.
- Solver core is separated from KLayout/Qt and renderer private internals.

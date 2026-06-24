# Process Planner Gap Audit

Last updated: 2026-06-24

## Contract Gaps

### Session JSON

- Canonical registry is now the runtime artifact interface. Legacy embedded images, drawings, and exports are converted only at integer-schema migration boundaries and are not hydrated back onto current session records.
- Measurement-owned annotation artifacts are generated through the render bridge on save and can be regenerated from the editor action; export and rasterizer failures are covered as structured result/warning paths with failed artifact repair metadata.
- Profilometry and ellipsometry compound captures save central artifact records for site images, annotation placeholders, and process-output placeholders; no runtime image/drawing compatibility wrappers are hydrated onto captures.
- Process-output regeneration stores solver summaries in canonical `ProcessOutputRecord` records. When session paths are configured, `ProcessOutputStore` writes JSON summary artifacts and updates central process-output artifact records to `present`; export failures become structured warnings.
- Reload coverage now proves parent capture plus child measurement canvas objects survive save/load.

### UI

- The editor dispatches commands, but the minimal Qt shell is not yet a complete production review UI.
- Some deferred actions still intentionally return unavailable results: PowerPoint build and some repair/export flows.
- Pending composite review actions now exist in the unified editor action layer for save, retake inner feature, retake site box, discard, and exit.
- KLayout-boundary line measurement, profilometry child-line capture, and ellipsometry child-point capture are covered with pure adapter smoke tests and opt-in live KLayout batch probes. The live lane passed against `C:\Users\edmun\AppData\Roaming\KLayout\klayout_app.exe` with `KLAYOUT_EXE` configured.

### Capture And Canvas Interaction

- Box capture is stable and covered.
- Measurement line capture now exists in the pure workflow layer.
- A KLayout-safe gesture adapter routes normalized Shift-drag line events into `LineCaptureTool`; release commits to saved child measurements or profilometry compound child lines based on durable workflow state, and restores overlays without source-layout mutation.
- Point capture is explicitly unavailable for general workflows, but the ellipsometry site-then-point child step routes through the shared compound capture service and KLayout gesture adapter without source-layout mutation.
- Parent site boxes remain active during child line capture in pure and KLayout-boundary adapter tests.

### Modes

- Built-in modes now have declarative `ModeDefinition` records in a pure `ModeRegistry`, including primitive capabilities, measurement support, editor groups, and adapter id.
- Profilometry Planner and Ellipsometry Planner declare `site_then_line` and `site_then_point` sequences, recipe policy, solver operation, metadata fields, and artifact roles as data.
- Mode-specific capture/review code must not be introduced while closing alpha gaps.
- Invalid custom modes now fail gracefully during session load: the session opens in `simple_capture`, the requested mode is preserved in `extensions.mode_validation`, and a stable warning/audit event is created.
- External custom-mode definitions can now be loaded from JSON folders as inert data and merged into the pure registry. App-level configuration, packaging, and live host discovery of those folders remain future work.

### Warnings And Diagnostics

- Missing and pending artifacts become warnings and repair tasks.
- Diagnostics services can inspect seams and snapshots.
- The Advanced Diagnostics controller/shell now shows active session, built-in/loaded mode IDs, artifact status counts, warning codes, missing artifact count, recent command names, and recent diagnostic event names.
- A polished end-user diagnostics dashboard remains future UI work, but the current fakeable shell exposes the required alpha-spine state.

## Highest-Impact Remaining Gaps

1. Wire external JSON custom-mode folders into app/release configuration so host installs can discover them without test-only calls.
2. Add richer process-output renderers beyond JSON summaries, such as profile images, stack tables, and cross-section image outputs.
3. Polished diagnostics dashboard UI beyond the current fakeable shell.
4. Full live Qt editor polish for artifact repair affordances.

## Smallest Next Slice

Keep expanding the process-aware compound spine without forking UI or persistence:

- keep `MPP_RUN_KLAYOUT_TESTS=1 python -m unittest tests.test_klayout_integration` passing with `KLAYOUT_EXE` configured,
- extend JSON process-output export into richer image/table renderers while keeping file writes behind persistence services.

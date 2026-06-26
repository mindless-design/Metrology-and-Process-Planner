# Testing Strategy

The synthetic process laboratory adds a fast feedback loop for geometry,
solver, rendering, and artifact-registry behavior without requiring UI state.

## Test Tiers

- Unit: pure Python model, validation, and extraction tests.
- Golden: solver and render-scene JSON snapshot tests.
- Integration: optional KLayout geometry/image smoke tests.
- Visual: manual render gallery generation.
- Slow: future full end-to-end synthetic GDS pipelines.

## Commands

```powershell
python tests/fixtures/gds/generate_process_planner_testchip.py
python tools/generate_synthetic_goldens.py
python tools/generate_render_gallery.py
pytest tests/test_synthetic_geometry_extraction.py
pytest tests/test_synthetic_solver_regression.py
pytest tests/test_synthetic_render_regression.py
pytest tests/test_synthetic_artifact_pipeline.py
pytest tests/integration -m klayout
```

Default CI should run unit, golden, and non-KLayout integration tests. KLayout
tests must remain opt-in or marked `klayout`; normal unit tests must not require
interactive KLayout.

## Failure Workflow

Snapshot tests write changed actual summaries to `tests/output/debug/` before
failing. Use those files to inspect:

- structure or recipe id
- operation that changed
- expected vs actual stack signature
- expected vs actual diagnostics
- expected vs actual scene metadata
- render/gallery artifact path

When behavior intentionally changes, regenerate goldens and review the JSON
diffs before committing them.

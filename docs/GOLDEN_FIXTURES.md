# Golden Fixtures

Synthetic golden fixtures are organized by purpose:

- `tests/fixtures/recipes/`: executable process recipe JSON fixtures.
- `tests/fixtures/synthetic_sessions/`: session fixtures tied to the synthetic GDS.
- `tests/fixtures/synthetic_sessions/broken/`: intentionally broken sessions.
- `tests/golden/solver/`: compact solver summary snapshots.
- `tests/golden/render/`: compact render-scene summary snapshots.
- `tests/output/debug/`: actual outputs written when snapshot assertions fail.

Refresh solver and render goldens after intentional behavior changes:

```powershell
python tools/generate_synthetic_goldens.py
```

When a golden changes, review the diff for material order, top-surface range,
diagnostics, render warnings, compression flags, and label counts. Do not update
goldens for unexplained changes.

Broken fixtures advertise expected repair diagnostics in their `metadata`:
`ARTIFACT_MISSING`, `RECIPE_MISSING`, `GEOMETRY_LAYER_MISSING`,
`ARTIFACT_STALE`, `MEASUREMENT_INVALID`, and `MODE_INVALID`.

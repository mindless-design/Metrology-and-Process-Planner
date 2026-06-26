# Synthetic Test GDS

The synthetic process testchip lives in `tests/fixtures/gds/`.

- Generator: `tests/fixtures/gds/generate_process_planner_testchip.py`
- GDS: `tests/fixtures/gds/process_planner_testchip.gds`
- Geometry sidecar: `tests/fixtures/gds/process_planner_testchip.geometry.json`
- Top cell: `PROCESS_PLANNER_TESTCHIP`
- Coordinates: microns
- Database unit: 1 nm

Regenerate with:

```powershell
python tests/fixtures/gds/generate_process_planner_testchip.py
```

The sidecar manifest is the pure Python extraction source of truth for fast
tests. Optional KLayout smoke tests can read the GDS directly.

## Structures

- `simple_line_space`: isolated lines and a dense line-space array.
- `trench_via_etch`: square vias, narrow trench, and wide trench.
- `isotropic_undercut`: sacrificial strip, release opening, narrow bridge.
- `conformal_liner_challenge`: narrow gap, wide gap, and vertical step.
- `cmp_planarization_density`: sparse block and dense local array.
- `profilometry_surface_test`: top surface step plus buried geometry.
- `fib_full_stack_test`: cut line with thick context and thin top markers.
- `point_stack_ellipsometry`: field, metal, overlap, and near-edge points.
- `label_stress_test`: adjacent narrow features for crowded labeling.
- `grid_capture_test`: two anchors and a repeated capture-site array.

The stable layer map is documented in `tests/fixtures/gds/README.md`.

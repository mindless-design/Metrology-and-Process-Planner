# Process Planner Synthetic Testchip

`generate_process_planner_testchip.py` creates `process_planner_testchip.gds`
and the matching `process_planner_testchip.geometry.json` manifest.

The top cell is `PROCESS_PLANNER_TESTCHIP`. Coordinates are deterministic and
expressed in microns; the GDS database unit is 1 nm.

## Stable Layer Map

| Layer | Name | Purpose |
| --- | --- | --- |
| 1/0 | ACTIVE | active silicon and field shapes |
| 2/0 | POLY | line-space and gate-like structures |
| 3/0 | CONTACT | via openings and contact cuts |
| 4/0 | METAL1 | metal line features |
| 5/0 | METAL2 | upper metal and overlap tests |
| 6/0 | VIA | via stack openings |
| 7/0 | TRENCH | trench and directional etch masks |
| 8/0 | LINER_TEST | conformal liner challenge geometry |
| 9/0 | CMP_DENSITY | CMP density-window structures |
| 10/0 | ALIGN | alignment and grid anchors |
| 11/0 | GRID | site array capture geometry |
| 12/0 | FIB_CUT_TEST | FIB full-stack cut targets |
| 13/0 | PROFILE_TEST | profilometry surface targets |
| 14/0 | POINT_STACK_TEST | ellipsometry point-stack targets |
| 15/0 | LABEL_STRESS_TEST | dense labels and leader stress |

## Structures

- `simple_line_space`: isolated rectangles and dense line-space array.
- `trench_via_etch`: square vias plus narrow and wide trench openings.
- `isotropic_undercut`: mask opening, sacrificial region, and narrow bridge.
- `conformal_liner_challenge`: narrow/wide trenches plus a vertical step.
- `cmp_planarization_density`: sparse block, dense array, and open field.
- `profilometry_surface_test`: surface step with buried metal variation.
- `fib_full_stack_test`: cut line across thick context and thin top films.
- `point_stack_ellipsometry`: field, metal, overlap, and near-edge locations.
- `label_stress_test`: many adjacent narrow features for crowded labels.
- `grid_capture_test`: two anchors and a repeated site array.

Regenerate with:

```powershell
python tests/fixtures/gds/generate_process_planner_testchip.py
```

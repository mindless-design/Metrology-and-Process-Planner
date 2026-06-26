# Solver Regression

The synthetic solver regression suite runs recipe JSON through the existing
`HybridCrossSectionSolver` and compares JSON-native summaries.

Run it with:

```powershell
pytest tests/test_synthetic_solver_regression.py
```

The summary checks:

- frame count
- final step id
- material set
- diagnostic codes
- stack signature by sampled x column
- top-surface min/max
- point and cutline sample counts

The first pinned recipes are:

- `simple_stack_recipe`
- `conformal_liner_recipe`
- `tapered_etch_recipe`
- `profilometry_surface_recipe`
- `fib_full_stack_recipe`

The broader recipe existence/validation test also covers patterned deposition,
directional etch, isotropic undercut, CMP, and process flow.

Specialized profile details that are not currently represented by the stable
recipe schema, such as sidewall angle or density coefficients, are preserved in
recipe `metadata`/`parameters` until the production schema supports them.

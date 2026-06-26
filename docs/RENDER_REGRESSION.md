# Render Regression

The synthetic render regression suite builds backend-independent
`CrossSectionSceneModel` summaries from solver output. It avoids brittle
pixel-perfect assertions.

Run it with:

```powershell
pytest tests/test_synthetic_render_regression.py
```

Generate the manual preview gallery with:

```powershell
python tools/generate_render_gallery.py
```

The gallery is written to `tests/output/render_gallery/index.html` with linked
scene JSON artifacts.

Current render cases:

- physical cross-section for the simple stack
- illustrative process cross-section for conformal liner
- profilometry surface filtering
- FIB full-stack compression
- process-flow frame rendering

The snapshot summaries check shape counts, material counts, labels, warnings,
compression metadata, compressed materials, and thin-layer exaggeration counts.

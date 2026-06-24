# Release Pipeline

The local release pipeline is designed to answer one question: is this package
safe to ship to KLayout users?

Run the default shippability check:

```powershell
python -m tools.release_check
```

Include real KLayout batch and GUI automation:

```powershell
$env:MPP_RUN_KLAYOUT_TESTS = "1"
$env:MPP_RUN_KLAYOUT_UI_TESTS = "1"
python -m tools.release_check --include-klayout
```

Build only the package archive:

```powershell
python -m tools.build_package
```

## What Release Check Verifies

- `grain.xml` version matches the Python package version.
- Static analysis passes.
- Unit tests pass.
- Python files compile.
- A clean KLayout package tree can be staged.
- A release zip can be built under `dist/`.
- Optional KLayout lanes pass when requested.

## Package Manifest

Release artifacts include only:

- `grain.xml`
- `README.md`
- `docs`
- `pymacros`
- `python`

Development files such as tests, caches, build outputs, and local tooling are
excluded from the package archive.


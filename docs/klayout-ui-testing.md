# KLayout UI And Integration Testing

The project uses opt-in KLayout integration tests so normal unit tests stay fast
and portable.

## Test Lanes

Pure Python:

```powershell
python -m unittest discover -s tests -t .
```

KLayout integration:

```powershell
$env:MPP_RUN_KLAYOUT_TESTS = "1"
python -m unittest tests.test_klayout_integration
```

KLayout GUI automation:

```powershell
$env:MPP_RUN_KLAYOUT_UI_TESTS = "1"
python -m unittest tests.test_klayout_ui_automation
```

Full local confidence:

```powershell
$env:MPP_RUN_KLAYOUT_TESTS = "1"
$env:MPP_RUN_KLAYOUT_UI_TESTS = "1"
python -m unittest discover -s tests -t .
python -m tools.static_analysis --fail-on-missing
```

## Executable Discovery

The integration runner tries, in order:

1. `KLAYOUT_EXE`
2. `klayout` on PATH
3. `klayout_app` on PATH
4. `%APPDATA%\KLayout\klayout_app.exe`

Set `KLAYOUT_EXE` if discovery misses your install:

```powershell
$env:KLAYOUT_EXE = "C:\Path\To\klayout_app.exe"
```

## Current Coverage

The first KLayout tests verify:

- KLayout can import the plugin package from the package-root `python` folder.
- KLayout exposes `pya`.
- The KLayout adapter boundary imports under KLayout.
- Plugin menu registration can run against a fake UI object model.
- Real GUI-mode KLayout can register the plugin menu in the live main window.
- Real GUI-mode KLayout can produce a main-window capability snapshot.

## Next UI Automation Step

The next layer should launch KLayout in editor mode with a temporary isolated
KLayout home and drive the real menu surface. Keep that slower lane separate
from import/adapter probes, because real UI automation is more timing-sensitive.

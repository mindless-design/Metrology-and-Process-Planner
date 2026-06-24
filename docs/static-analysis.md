# Static Analysis

The project has two analysis layers:

1. Always-on stdlib gates in `tools.quality_gates`.
2. Optional third-party analysis in `tools.static_analysis`.

Run the full optional suite with:

```powershell
python -m tools.static_analysis
```

After installing dev dependencies, make missing tools fail too:

```powershell
python -m tools.static_analysis --fail-on-missing
```

## Tool Roles

`ruff`
: Fast linting for imports, bug-prone patterns, modernization, naming, and
selected docstring conventions.

`mypy`
: Static typing for the pure Python core. Dynamic KLayout and Qt integration
gets narrower overrides because those APIs are runtime-provided.

`xenon` and `radon`
: Cyclomatic-complexity and maintainability checks. These prevent "one more if"
from quietly turning workflow controllers into knots.

`interrogate`
: Docstring coverage visibility. The custom gate enforces public summaries;
interrogate gives broader coverage feedback.

`import-linter`
: Architectural import contracts, especially the rule that domain code must not
depend on UI, infrastructure, or KLayout.

`vulture`
: Dead-code hints. Treat findings as review prompts because Qt/KLayout callbacks
and plugin entrypoints can be dynamic.

## Dynamic Boundary Policy

The core package should be statically boring: explicit types, no hidden globals,
and imports that follow the architecture.

Dynamic behavior belongs near the edge:

- `ui`
- `infrastructure/klayout`
- plugin bootstrap macros

For those areas, prefer small adapter protocols and `typing.TYPE_CHECKING`
imports. Add vulture whitelist entries only for real dynamic entrypoints, not to
silence ordinary unused code.

# Quality Gates

Run the project-specific quality gate with:

```powershell
python -m tools.quality_gates
```

The same gate is also enforced by the unit test suite.

## Budgets

`MPP001`
: Source files must stay at or below 220 lines. Test files must stay at or
below 180 lines. Split by responsibility before adding more behavior.

`MPP002`
: A module may define at most 12 public classes or functions. If a file needs
more, create a package and re-export the stable API from `__init__.py`.

`MPP003`
: Every public production module, class, function, and method needs a real
docstring summary. The summary must be at least 12 characters, end with a
period, and not be a placeholder.

`MPP004`
: Functions and methods must stay at or below 50 lines.

`MPP005`
: Classes must stay at or below 140 lines.

## Why These Rules Exist

These gates are not style theater. They are tripwires against the exact failure
mode this rebuild is avoiding: one file quietly becoming responsible for domain
logic, UI state, persistence, rendering, and KLayout runtime behavior.

When a gate fails, the preferred fix is usually to name the missing concept and
move it into a smaller module.


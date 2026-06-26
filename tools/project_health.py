"""Run the complete project self-audit health check."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from metrology_process_planner.diagnostics.diagnostics_project import (  # noqa: E402
    ProjectDiagnosticsBundle,
)
from metrology_process_planner.infrastructure.validation_models import (  # noqa: E402
    HealthCheckItem,
    HealthCheckReport,
    ValidationReport,
)


def build_health_report(project_root: Path = PROJECT_ROOT) -> HealthCheckReport:
    """Build the complete project health report."""

    from metrology_process_planner.infrastructure.project_validators import (
        validate_commands,
        validate_fixture_sessions,
        validate_modes,
        validate_render_profiles,
    )
    from metrology_process_planner.infrastructure.timing import TimingCollector
    from metrology_process_planner.testing.fixture_library import fixture_session_paths

    collector = TimingCollector()
    reports: list[ValidationReport] = []
    with collector.measure("mode validation"):
        reports.append(validate_modes())
    with collector.measure("command validation"):
        reports.append(validate_commands())
    with collector.measure("render profile validation"):
        reports.append(validate_render_profiles())
    with collector.measure("fixture validation"):
        reports.append(validate_fixture_sessions(fixture_session_paths(project_root)))
    items = tuple(_item(report) for report in reports)
    return HealthCheckReport(items, tuple(reports))


def build_diagnostics_bundle(project_root: Path = PROJECT_ROOT) -> ProjectDiagnosticsBundle:
    """Build an exportable diagnostics bundle for the current checkout."""

    from metrology_process_planner.devtools import build_developer_catalog
    from metrology_process_planner.diagnostics.diagnostics_project import estimate_memory_usage
    from metrology_process_planner.diagnostics.diagnostics_snapshots import (
        build_diagnostics_snapshot,
    )
    from metrology_process_planner.infrastructure.timing import TimingCollector

    collector = TimingCollector()
    with collector.measure("project health check"):
        health = build_health_report(project_root)
    catalog = build_developer_catalog()
    snapshot = build_diagnostics_snapshot(project_root)
    return ProjectDiagnosticsBundle(
        snapshot=snapshot,
        health=health,
        validation_reports=health.reports,
        timings=collector.metrics(),
        memory_usage_estimate_bytes=estimate_memory_usage(catalog.to_dict()),
    )


def main(argv: Optional[list[str]] = None) -> int:
    """Run the project health check from the command line."""

    parser = argparse.ArgumentParser(description="Run the project health check.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--bundle", type=Path, help="Optional diagnostics bundle output path.")
    args = parser.parse_args(argv)
    bundle = build_diagnostics_bundle(PROJECT_ROOT)
    if args.bundle:
        bundle.export(args.bundle)
    if args.json:
        print(json.dumps(bundle.health.to_dict(), indent=2))
    else:
        _print_human(bundle.health)
    return 0 if bundle.health.score == 100 else 1


def _item(report: ValidationReport) -> HealthCheckItem:
    return HealthCheckItem(report.subject, report.ok, len(report.issues))


def _print_human(report: HealthCheckReport) -> None:
    print("Project Health Check")
    for item in report.items:
        mark = "OK" if item.passed else "FAIL"
        suffix = "" if item.issue_count == 0 else f" ({item.issue_count} issue(s))"
        print(f"{mark} {item.name}{suffix}")
    print(f"\nOverall Health: {report.score}%")


if __name__ == "__main__":
    raise SystemExit(main())

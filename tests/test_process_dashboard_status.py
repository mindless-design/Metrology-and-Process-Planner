import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import ProcessContext, WarningRecord
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from tests.process_context_fixtures import dashboard_field
from tests.process_context_fixtures import session as base_session


class ProcessDashboardStatusTests(unittest.TestCase):
    def test_dashboard_statuses_use_open_process_warning_codes(self) -> None:
        warning = WarningRecord(
            "warn-process_recipe_file_not_found",
            "Recipe file was not found.",
            source="process_context",
            code="PROCESS_RECIPE_FILE_NOT_FOUND",
        )
        solver = WarningRecord(
            "warn-solver_backend_unavailable",
            "Solver backend unavailable.",
            source="process_context",
            code="SOLVER_BACKEND_UNAVAILABLE",
        )
        context = ProcessContext(
            recipe_path="missing.json",
            solver_backend="HybridCrossSectionSolver",
            warning_ids=(warning.id, solver.id),
        )
        document = SessionDocumentBuilder().build(
            replace(base_session(), process_context=context, warnings=(warning, solver))
        )

        self.assertEqual("missing", dashboard_field(document, "process_recipe"))
        self.assertEqual("unavailable", dashboard_field(document, "process_solver"))
        self.assertEqual("2", dashboard_field(document, "process_warning_count"))

    def test_dashboard_warning_count_ignores_resolved_warnings(self) -> None:
        warning = WarningRecord(
            "warn-process_recipe_missing",
            "No recipe.",
            source="process_context",
            code="PROCESS_RECIPE_MISSING",
            status="ignored",
        )
        context = ProcessContext(warning_ids=(warning.id,))
        document = SessionDocumentBuilder().build(
            replace(base_session(), process_context=context, warnings=(warning,))
        )

        self.assertEqual("none", dashboard_field(document, "process_recipe"))
        self.assertEqual("0", dashboard_field(document, "process_warning_count"))


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.workflows.process_output_requests import SolverInputBuilder
from tests.process_context_fixtures import custom_process_capture_session
from tests.process_output_fixtures import profile_session_with_recipe


class ProcessOutputRequestBuilderTests(unittest.TestCase):
    def test_solver_input_builder_maps_process_modes_to_operations_and_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            session = profile_session_with_recipe(Path(folder))
            capture = session.captures[0]
            builder = SolverInputBuilder()

            request = builder.build_request(session, capture)
            solver_input = builder.build(session, capture, _result_recipe(session))

        self.assertEqual("line_profile", request.operation)
        self.assertEqual("line", request.geometry_kind)
        self.assertEqual("profilometry_surface_profile", request.render_profile)
        self.assertEqual(1.0, solver_input.options.cutline_x_min)
        self.assertEqual(9.0, solver_input.options.cutline_x_max)

    def test_solver_input_builder_supports_fib_and_process_flow_requests(self) -> None:
        fib_session = custom_process_capture_session()
        fib_request = SolverInputBuilder().build_request(fib_session, fib_session.captures[0])
        flow_session = custom_process_capture_session()
        flow_capture = flow_session.captures[0]
        flow_capture = type(flow_capture).from_dict(
            {
                **flow_capture.to_dict(),
                "extensions": {
                    "process_flow": {
                        "process_context_ref": "process_context.active",
                        "solver_request": {
                            "operation": "process_flow_frames",
                            "render_profile": "process_flow_frame",
                        },
                    }
                },
            }
        )

        flow_request = SolverInputBuilder().build_request(flow_session, flow_capture)

        self.assertEqual("full_stack_compressed", fib_request.operation)
        self.assertEqual(("full_stack_compressed_image",), fib_request.output_roles)
        self.assertEqual("process_flow_frames", flow_request.operation)
        self.assertEqual(("process_flow_frame",), flow_request.output_roles)


def _result_recipe(session):
    from metrology_process_planner.domains.process import ProcessRecipe

    return ProcessRecipe.from_dict(
        json.loads(Path(session.process_context.recipe_path).read_text())
    )


if __name__ == "__main__":
    unittest.main()

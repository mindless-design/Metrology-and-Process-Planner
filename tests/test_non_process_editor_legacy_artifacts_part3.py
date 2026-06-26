import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
)
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from tests.editor_render_fixtures import session


def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class NonProcessEditorLegacyArtifactTestsPart3(unittest.TestCase):
    def test_recipe_free_pending_compound_metadata_hides_process_context(self) -> None:
        source = session()
        pending = source.pending_captures[0]
        source = replace(
            source,
            pending_captures=(
                replace(
                    pending,
                    metadata={
                        "label": "Compound Site",
                        "compound": {
                            "child_role": "feature",
                            "feature": {"id": "feature-001"},
                            "mode_id": source.mode.value,
                        },
                    },
                ),
            ),
        )
        document = SessionDocumentBuilder().build(source)
        item = document.items_by_id["pending:pending-001"]

        fields = DefaultSessionModeAdapter().metadata_fields(document.session, item)

        self.assertNotIn("process_context_ref", {field.key for field in fields})

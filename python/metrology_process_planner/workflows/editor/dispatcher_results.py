"""Result contracts for editor action dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.measurement_completion import PostActionPrompt


@dataclass(frozen=True)
class EditorActionResult:
    """Result returned after dispatching one editor action."""

    status: str
    document: SessionDocument
    message: str = ""
    output_path: Optional[Path] = None
    post_action_prompt: PostActionPrompt | None = None

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .loop import Run
from .control_state import ControlState


def save_checkpoint(run: Run, control_state: ControlState, path: str | Path) -> None:
    """Write down exactly enough to resume later: which run, which step
    comes next, and the control state at the moment we stopped."""
    data = {
        "run_id": run.run_id,
        "agent_name": run.agent_name,
        "next_step_index": run.next_step_index,
        "control_state": control_state.state.value,
        "state_version": control_state.state_version,
    }
    Path(path).write_text(json.dumps(data, indent=2))


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())

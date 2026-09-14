from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .control_state import ControlState

# Deliberately generic: this module knows nothing about any specific agent's
# Run/Step types (agent-runtime depends on control-sdk, never the other way
# around) — it just needs a run_id and "which step comes next."


def save_checkpoint(run_id: str, next_step_index: int, control_state: ControlState, path: str | Path) -> None:
    """Write down exactly enough to resume later: which run, which step
    comes next, and the control state at the moment we stopped."""
    data = {
        "run_id": run_id,
        "next_step_index": next_step_index,
        "control_state": control_state.state.value,
        "state_version": control_state.state_version,
    }
    Path(path).write_text(json.dumps(data, indent=2))


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())

from __future__ import annotations

from .control_state import ControlState


class CancellationToken:
    """Handed to a step's action only if it opts in. Checking is_cancelled
    never mutates control_state — only the safe-point logic in the agent's
    loop actually confirms a stop. This just lets a long-running operation
    ask "should I stop?" partway through its own work, instead of only
    being caught at the step boundary.

    CLAUDE.md section 8: "Pass a cancellation token only to components that
    support it." — an operation that never checks this token will still run
    to completion; that is correct, not a bug."""

    def __init__(self, control_state: ControlState) -> None:
        self._control_state = control_state

    @property
    def is_cancelled(self) -> bool:
        return self._control_state.is_stop_requested()

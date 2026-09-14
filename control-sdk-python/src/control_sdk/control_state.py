from __future__ import annotations

from enum import Enum


class State(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSE_REQUESTED = "PAUSE_REQUESTED"
    PAUSED = "PAUSED"
    RESUME_REQUESTED = "RESUME_REQUESTED"
    STOP_REQUESTED = "STOP_REQUESTED"
    STOPPED = "STOPPED"
    # Not reached by any transition below — set by the heartbeat layer
    # (heartbeat.py) when the last heartbeat is stale. Never guessed.
    UNKNOWN = "UNKNOWN"


# CLAUDE.md section 9. Any transition not listed here is illegal.
_ALLOWED: dict[State, set[State]] = {
    State.ACTIVE: {State.PAUSE_REQUESTED, State.STOP_REQUESTED},
    State.PAUSE_REQUESTED: {State.PAUSED, State.STOP_REQUESTED},
    State.PAUSED: {State.RESUME_REQUESTED, State.STOP_REQUESTED},
    State.RESUME_REQUESTED: {State.ACTIVE},
    State.STOP_REQUESTED: {State.STOPPED},
    State.STOPPED: {State.RESUME_REQUESTED},
}


class IllegalTransition(Exception):
    """Raised when a transition isn't in the state machine. Never silently
    ignored and never coerced to the nearest legal state — the caller must
    decide what an illegal request means (e.g. reject the command)."""


class ControlState:
    """In-memory control state for one agent/run. No network, no
    persistence of its own (see checkpoint.py) — just the legal-transition
    logic, kept small enough to test exhaustively on its own.

    state_version increments on every successful transition. This is the
    same counter the Control API will later use for optimistic concurrency
    (CLAUDE.md section 11: expected_state_version)."""

    def __init__(self) -> None:
        self.state: State = State.ACTIVE
        self.state_version: int = 0

    def request_pause(self) -> None:
        self._transition(State.PAUSE_REQUESTED)

    def confirm_paused(self) -> None:
        self._transition(State.PAUSED)

    def request_stop(self) -> None:
        self._transition(State.STOP_REQUESTED)

    def confirm_stopped(self) -> None:
        self._transition(State.STOPPED)

    def request_resume(self) -> None:
        self._transition(State.RESUME_REQUESTED)

    def confirm_resumed(self) -> None:
        self._transition(State.ACTIVE)

    def is_pause_requested(self) -> bool:
        return self.state == State.PAUSE_REQUESTED

    def is_stop_requested(self) -> bool:
        return self.state == State.STOP_REQUESTED

    def _transition(self, target: State) -> None:
        allowed = _ALLOWED.get(self.state, set())
        if target not in allowed:
            raise IllegalTransition(f"cannot go from {self.state} to {target}")
        self.state = target
        self.state_version += 1

    @classmethod
    def from_persisted(cls, state: State, state_version: int) -> "ControlState":
        """Rebuild state after a restart, from a checkpoint file — not a
        transition (no legality check), just restoring a fact that was
        already true before the process stopped."""
        cs = cls()
        cs.state = state
        cs.state_version = state_version
        return cs

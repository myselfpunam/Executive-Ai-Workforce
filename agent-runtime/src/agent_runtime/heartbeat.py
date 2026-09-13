from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .control_state import ControlState, State


@dataclass(frozen=True)
class Heartbeat:
    """One "I'm alive, here's my state" signal. This is what the dashboard
    will eventually poll/subscribe to — never a live object reference, just
    a plain snapshot with a timestamp."""

    state: str
    state_version: int
    active_run_id: str | None
    emitted_at: str  # ISO 8601, UTC


def emit_heartbeat(control_state: ControlState, active_run_id: str | None) -> Heartbeat:
    return Heartbeat(
        state=control_state.state.value,
        state_version=control_state.state_version,
        active_run_id=active_run_id,
        emitted_at=datetime.now(timezone.utc).isoformat(),
    )


def _age_seconds(heartbeat: Heartbeat, now: datetime) -> float:
    emitted_at = datetime.fromisoformat(heartbeat.emitted_at)
    return (now - emitted_at).total_seconds()


def is_fresh(heartbeat: Heartbeat | None, max_age_seconds: float, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if heartbeat is None:
        return False
    return _age_seconds(heartbeat, now) <= max_age_seconds


def effective_state(heartbeat: Heartbeat | None, max_age_seconds: float, now: datetime | None = None) -> str:
    """What an outside observer (dashboard, reconciler) should treat the
    agent's state as, right now. CLAUDE.md section 9: "If heartbeat is
    stale, state is UNKNOWN. Never guess." — so a missing or stale
    heartbeat is reported as UNKNOWN, never as the last state we happened
    to see."""
    if not is_fresh(heartbeat, max_age_seconds, now):
        return State.UNKNOWN.value
    return heartbeat.state

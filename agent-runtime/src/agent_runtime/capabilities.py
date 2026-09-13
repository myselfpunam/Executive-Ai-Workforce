from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .heartbeat import Heartbeat, is_fresh


@dataclass(frozen=True)
class Capabilities:
    """The "badge" an agent wears, from CLAUDE.md section 12. A real
    provider-hosted/opaque agent might have all three flags False — that's
    CONTROL_UNSUPPORTED, not an error."""

    pause_supported: bool
    stop_supported: bool
    resume_supported: bool
    checkpoint_mode: str
    max_checkpoint_delay_ms: int
    adapter_version: str


def demo_agent_capabilities() -> Capabilities:
    """What our deterministic demo agent can do — everything, since it's
    built with control_state + checkpoint support from the start."""
    return Capabilities(
        pause_supported=True,
        stop_supported=True,
        resume_supported=True,
        checkpoint_mode="SAFE_POINT",
        max_checkpoint_delay_ms=2000,
        adapter_version="0.1.0",
    )


_ACTION_FLAG = {
    "PAUSE": "pause_supported",
    "STOP": "stop_supported",
    "RESUME": "resume_supported",
}


def can_issue(
    action: str,
    capabilities: Capabilities,
    heartbeat: Heartbeat | None,
    max_age_seconds: float,
    now: datetime | None = None,
) -> bool:
    """The UI rule from CLAUDE.md section 12: enable a control only if the
    capability is supported AND the heartbeat is fresh. (Role and
    state_version checks join this once a real UI/API exist.)"""
    flag_name = _ACTION_FLAG.get(action)
    if flag_name is None:
        return False
    if not getattr(capabilities, flag_name):
        return False
    return is_fresh(heartbeat, max_age_seconds, now)

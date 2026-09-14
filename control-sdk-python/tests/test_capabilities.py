from datetime import datetime, timedelta

from control_sdk.capabilities import Capabilities, can_issue
from control_sdk.control_state import ControlState
from control_sdk.heartbeat import emit_heartbeat


def _all_supported() -> Capabilities:
    return Capabilities(
        pause_supported=True,
        stop_supported=True,
        resume_supported=True,
        checkpoint_mode="SAFE_POINT",
        max_checkpoint_delay_ms=2000,
        adapter_version="0.1.0",
    )


def test_all_actions_allowed_when_supported_and_heartbeat_fresh():
    caps = _all_supported()
    hb = emit_heartbeat(ControlState(), active_run_id=None)
    now = datetime.fromisoformat(hb.emitted_at)

    assert can_issue("PAUSE", caps, hb, max_age_seconds=30, now=now) is True
    assert can_issue("STOP", caps, hb, max_age_seconds=30, now=now) is True
    assert can_issue("RESUME", caps, hb, max_age_seconds=30, now=now) is True


def test_unsupported_capability_blocks_the_action_even_with_a_fresh_heartbeat():
    caps = Capabilities(
        pause_supported=True,
        stop_supported=False,  # e.g. an opaque, provider-hosted agent
        resume_supported=True,
        checkpoint_mode="NONE",
        max_checkpoint_delay_ms=0,
        adapter_version="0.0.1",
    )
    hb = emit_heartbeat(ControlState(), active_run_id=None)
    now = datetime.fromisoformat(hb.emitted_at)

    assert can_issue("STOP", caps, hb, max_age_seconds=30, now=now) is False


def test_stale_heartbeat_blocks_the_action_even_when_supported():
    caps = _all_supported()
    hb = emit_heartbeat(ControlState(), active_run_id=None)
    long_after = datetime.fromisoformat(hb.emitted_at) + timedelta(seconds=120)

    assert can_issue("PAUSE", caps, hb, max_age_seconds=30, now=long_after) is False


def test_unknown_action_is_never_allowed():
    caps = _all_supported()
    hb = emit_heartbeat(ControlState(), active_run_id=None)
    now = datetime.fromisoformat(hb.emitted_at)

    assert can_issue("DELETE_EVERYTHING", caps, hb, max_age_seconds=30, now=now) is False

from datetime import datetime, timedelta

from agent_runtime.capabilities import Capabilities, can_issue, demo_agent_capabilities
from agent_runtime.control_state import ControlState
from agent_runtime.heartbeat import emit_heartbeat


def test_demo_agent_supports_all_three_actions_with_a_fresh_heartbeat():
    caps = demo_agent_capabilities()
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
    caps = demo_agent_capabilities()
    hb = emit_heartbeat(ControlState(), active_run_id=None)
    long_after = datetime.fromisoformat(hb.emitted_at) + timedelta(seconds=120)

    assert can_issue("PAUSE", caps, hb, max_age_seconds=30, now=long_after) is False


def test_unknown_action_is_never_allowed():
    caps = demo_agent_capabilities()
    hb = emit_heartbeat(ControlState(), active_run_id=None)
    now = datetime.fromisoformat(hb.emitted_at)

    assert can_issue("DELETE_EVERYTHING", caps, hb, max_age_seconds=30, now=now) is False

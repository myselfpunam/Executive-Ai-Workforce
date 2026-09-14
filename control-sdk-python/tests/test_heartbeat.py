from datetime import datetime, timedelta

from control_sdk.control_state import ControlState, State
from control_sdk.heartbeat import effective_state, emit_heartbeat


def test_fresh_heartbeat_reports_the_real_state():
    control_state = ControlState()
    control_state.request_pause()
    control_state.confirm_paused()

    hb = emit_heartbeat(control_state, active_run_id="run_abc")
    now = datetime.fromisoformat(hb.emitted_at)  # "checked right now"

    assert effective_state(hb, max_age_seconds=30, now=now) == State.PAUSED.value


def test_stale_heartbeat_reports_unknown_not_the_old_state():
    control_state = ControlState()  # ACTIVE
    hb = emit_heartbeat(control_state, active_run_id="run_abc")

    long_after = datetime.fromisoformat(hb.emitted_at) + timedelta(seconds=120)

    # Even though the last known state was ACTIVE, a stale heartbeat must
    # NOT be reported as "probably still ACTIVE" — that would be a guess.
    assert effective_state(hb, max_age_seconds=30, now=long_after) == State.UNKNOWN.value


def test_missing_heartbeat_reports_unknown():
    assert effective_state(None, max_age_seconds=30) == State.UNKNOWN.value

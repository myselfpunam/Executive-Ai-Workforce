import pytest

from agent_runtime.control_state import ControlState, IllegalTransition, State


def test_starts_active_with_version_zero():
    cs = ControlState()
    assert cs.state == State.ACTIVE
    assert cs.state_version == 0


def test_full_pause_then_resume_cycle():
    cs = ControlState()

    cs.request_pause()
    assert cs.state == State.PAUSE_REQUESTED

    cs.confirm_paused()
    assert cs.state == State.PAUSED

    cs.request_resume()
    assert cs.state == State.RESUME_REQUESTED

    cs.confirm_resumed()
    assert cs.state == State.ACTIVE
    assert cs.state_version == 4


def test_full_stop_then_resume_cycle_re_enables_future_work():
    cs = ControlState()

    cs.request_stop()
    cs.confirm_stopped()
    assert cs.state == State.STOPPED

    # CLAUDE.md section 7/9: resume after STOP re-enables future work only.
    # It is still just a state transition here — nothing about "the old run
    # continuing" is implied, because a stopped run is terminal.
    cs.request_resume()
    cs.confirm_resumed()
    assert cs.state == State.ACTIVE


def test_stop_can_interrupt_a_pause_in_progress():
    cs = ControlState()
    cs.request_pause()
    cs.request_stop()  # allowed even mid-pause-request
    assert cs.state == State.STOP_REQUESTED


def test_illegal_transition_is_rejected_not_guessed():
    cs = ControlState()

    with pytest.raises(IllegalTransition):
        cs.confirm_paused()  # can't confirm a pause that was never requested

    # rejecting the illegal call must not have mutated state
    assert cs.state == State.ACTIVE
    assert cs.state_version == 0


def test_cannot_pause_while_already_stopped():
    cs = ControlState()
    cs.request_stop()
    cs.confirm_stopped()

    with pytest.raises(IllegalTransition):
        cs.request_pause()

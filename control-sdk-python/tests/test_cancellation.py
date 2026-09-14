from control_sdk.cancellation import CancellationToken
from control_sdk.control_state import ControlState


def test_token_reflects_a_stop_request():
    control_state = ControlState()
    token = CancellationToken(control_state)

    assert token.is_cancelled is False

    control_state.request_stop()
    assert token.is_cancelled is True


def test_checking_the_token_never_mutates_control_state():
    control_state = ControlState()
    control_state.request_stop()
    token = CancellationToken(control_state)

    version_before = control_state.state_version
    for _ in range(5):
        _ = token.is_cancelled  # checking it repeatedly must be a pure read

    assert control_state.state_version == version_before
    assert control_state.is_stop_requested()  # still just STOP_REQUESTED, not confirmed

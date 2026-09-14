from control_sdk.checkpoint import load_checkpoint, save_checkpoint
from control_sdk.control_state import ControlState


def test_save_then_load_round_trips_the_right_fields(tmp_path):
    control_state = ControlState()
    control_state.request_pause()
    control_state.confirm_paused()

    path = tmp_path / "run.checkpoint.json"
    save_checkpoint(run_id="run_123", next_step_index=2, control_state=control_state, path=path)

    saved = load_checkpoint(path)
    assert saved == {
        "run_id": "run_123",
        "next_step_index": 2,
        "control_state": "PAUSED",
        "state_version": control_state.state_version,
    }

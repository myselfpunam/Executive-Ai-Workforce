from agent_runtime.checkpoint import load_checkpoint, save_checkpoint
from agent_runtime.control_state import ControlState, State
from agent_runtime.loop import DemoAgent, Step


def build_four_step_agent(control_state: ControlState):
    def step_b_action():
        control_state.request_pause()  # simulate: boss clicks Pause during step-b
        return {"ok": True}

    return DemoAgent(
        name="test-agent",
        steps=[
            Step("step-a", lambda: {"ok": True}),
            Step("step-b", step_b_action),
            Step("step-c", lambda: {"ok": True}),
            Step("step-d", lambda: {"ok": True}),
        ],
    )


def test_pausing_writes_a_checkpoint_file_with_the_right_next_step(tmp_path):
    control_state = ControlState()
    agent = build_four_step_agent(control_state)
    checkpoint_path = tmp_path / "run.checkpoint.json"

    run = agent.run(control_state=control_state, checkpoint_path=str(checkpoint_path))

    assert run.status == "PAUSED"
    assert checkpoint_path.exists()

    saved = load_checkpoint(checkpoint_path)
    assert saved["run_id"] == run.run_id
    assert saved["next_step_index"] == 2  # step-c is next; a and b already ran
    assert saved["control_state"] == "PAUSED"


def test_full_pause_restart_resume_cycle_does_not_redo_finished_steps(tmp_path):
    # --- before the "restart": pause partway through ---
    control_state = ControlState()
    agent = build_four_step_agent(control_state)
    checkpoint_path = tmp_path / "run.checkpoint.json"

    first_run = agent.run(control_state=control_state, checkpoint_path=str(checkpoint_path))
    assert first_run.status == "PAUSED"

    # --- "restart": pretend this is a brand new process. All we have is
    # the checkpoint file on disk — no in-memory objects survive. ---
    saved = load_checkpoint(checkpoint_path)
    restored_control_state = ControlState.from_persisted(
        state=State(saved["control_state"]),
        state_version=saved["state_version"],
    )

    # RESUME command arrives: PAUSED -> RESUME_REQUESTED -> ACTIVE
    restored_control_state.request_resume()
    restored_control_state.confirm_resumed()

    # a fresh DemoAgent object (new process would rebuild this from code,
    # not from the checkpoint) — but note we still need step-b's closure
    # for this test agent; a real agent's steps come from its own code.
    resumed_agent = build_four_step_agent(restored_control_state)

    second_run = resumed_agent.run(control_state=restored_control_state, resume=saved)

    assert second_run.status == "COMPLETED"
    assert second_run.run_id == first_run.run_id  # same run, continued — not a new one

    event_types = [e.type for e in second_run.events]
    assert event_types == [
        "run.resumed",
        "step.started",
        "step.completed",
        "step.started",
        "step.completed",
        "run.completed",
    ]
    resumed_step_names = [e.data["name"] for e in second_run.events if e.type == "step.started"]
    assert resumed_step_names == ["step-c", "step-d"]  # step-a and step-b were NOT redone

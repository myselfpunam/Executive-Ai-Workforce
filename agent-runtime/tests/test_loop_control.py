from control_sdk.control_state import ControlState, State

from agent_runtime.loop import DemoAgent, Step


def test_pause_requested_before_run_stops_before_any_step_starts():
    control_state = ControlState()
    control_state.request_pause()  # simulate: boss clicked Pause first

    agent = DemoAgent(name="test-agent", steps=[Step("step-a", lambda: {"ok": True})])

    run = agent.run(control_state=control_state)

    assert run.status == "PAUSED"
    assert control_state.state == State.PAUSED
    assert [e.type for e in run.events] == ["run.started", "run.paused"]


def test_pause_requested_mid_step_stops_after_that_step_not_before():
    control_state = ControlState()

    def step_b_action():
        # simulate: boss clicks Pause WHILE this step is running
        control_state.request_pause()
        return {"ok": True}

    agent = DemoAgent(
        name="test-agent",
        steps=[
            Step("step-a", lambda: {"ok": True}),
            Step("step-b", step_b_action),
            Step("step-c", lambda: {"ok": True}),  # must never run
        ],
    )

    run = agent.run(control_state=control_state)

    assert run.status == "PAUSED"
    event_types = [e.type for e in run.events]
    assert event_types == [
        "run.started",
        "step.started",
        "step.completed",
        "step.started",
        "step.completed",
        "run.paused",
    ]
    started_step_names = [e.data["name"] for e in run.events if e.type == "step.started"]
    assert started_step_names == ["step-a", "step-b"]
    assert "step-c" not in started_step_names


def test_stop_requested_cancels_the_run_immediately():
    control_state = ControlState()
    control_state.request_stop()

    agent = DemoAgent(name="test-agent", steps=[Step("step-a", lambda: {"ok": True})])

    run = agent.run(control_state=control_state)

    assert run.status == "CANCELLED"
    assert control_state.state == State.STOPPED
    assert [e.type for e in run.events] == ["run.started", "run.cancelled"]


def test_a_run_with_no_pause_or_stop_still_completes_normally():
    agent = DemoAgent(name="test-agent", steps=[Step("step-a", lambda: {"ok": True})])

    run = agent.run()  # no control_state passed — defaults to a fresh ACTIVE one

    assert run.status == "COMPLETED"

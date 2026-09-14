from control_sdk.control_state import ControlState

from agent_runtime.loop import DemoAgent, Step


def test_step_without_token_support_ignores_a_mid_step_stop_and_finishes_its_own_work():
    control_state = ControlState()

    def long_step_no_token():
        chunks_done = 0
        for i in range(5):
            if i == 2:
                control_state.request_stop()  # stop arrives mid-way
            chunks_done += 1  # never checks — keeps going regardless
        return {"chunks_processed": chunks_done}

    agent = DemoAgent(name="test-agent", steps=[Step("bulk-copy", long_step_no_token)])
    run = agent.run(control_state=control_state)

    step_completed = next(e for e in run.events if e.type == "step.completed")
    assert step_completed.data["chunks_processed"] == 5  # did all the work anyway
    assert run.status == "CANCELLED"  # but still stopped at the NEXT safe point


def test_step_with_token_support_stops_early_when_cancellation_is_requested_mid_step():
    control_state = ControlState()

    def long_step_with_token(token):
        chunks_done = 0
        for i in range(5):
            if i == 2:
                control_state.request_stop()  # stop arrives mid-way
            if token.is_cancelled:
                break
            chunks_done += 1
        return {"chunks_processed": chunks_done}

    agent = DemoAgent(
        name="test-agent",
        steps=[Step("bulk-copy", long_step_with_token, accepts_cancellation_token=True)],
    )
    run = agent.run(control_state=control_state)

    step_completed = next(e for e in run.events if e.type == "step.completed")
    assert step_completed.data["chunks_processed"] == 2  # bailed out early, didn't waste work
    assert run.status == "CANCELLED"

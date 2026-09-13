from agent_runtime.loop import DemoAgent, Step


def test_successful_run_emits_expected_event_sequence():
    agent = DemoAgent(
        name="test-agent",
        steps=[
            Step("step-a", lambda: {"ok": True}),
            Step("step-b", lambda: {"ok": True}),
        ],
    )

    run = agent.run()

    assert run.status == "COMPLETED"
    event_types = [e.type for e in run.events]
    assert event_types == [
        "run.started",
        "step.started",
        "step.completed",
        "step.started",
        "step.completed",
        "run.completed",
    ]


def test_failing_step_stops_the_run_and_marks_it_failed():
    def boom():
        raise ValueError("simulated failure")

    agent = DemoAgent(
        name="test-agent",
        steps=[
            Step("step-a", lambda: {"ok": True}),
            Step("step-b", boom),
            Step("step-c", lambda: {"ok": True}),
        ],
    )

    run = agent.run()

    assert run.status == "FAILED"
    event_types = [e.type for e in run.events]
    assert event_types == [
        "run.started",
        "step.started",
        "step.completed",
        "step.started",
        "step.failed",
        "run.failed",
    ]
    failed_event = run.events[-2]
    assert failed_event.data["error"] == "simulated failure"


def test_each_run_gets_a_unique_run_id():
    agent = DemoAgent(name="test-agent", steps=[Step("only", lambda: {})])

    run_1 = agent.run()
    run_2 = agent.run()

    assert run_1.run_id != run_2.run_id

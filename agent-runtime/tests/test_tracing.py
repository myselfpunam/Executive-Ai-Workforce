from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from agent_runtime.loop import DemoAgent, Step
from agent_runtime.tracing import build_tracer_provider


def _traced_agent(name: str, steps: list[Step]):
    exporter = InMemorySpanExporter()
    provider = build_tracer_provider(exporter=exporter)
    tracer = provider.get_tracer("test")
    agent = DemoAgent(name=name, steps=steps, tracer=tracer)
    return agent, exporter, provider


def test_a_successful_run_produces_one_run_span_and_one_span_per_step():
    agent, exporter, provider = _traced_agent(
        "traced-agent",
        [Step("step-a", lambda: {"ok": True}), Step("step-b", lambda: {"ok": True})],
    )

    agent.run()
    provider.force_flush()

    span_names = [s.name for s in exporter.get_finished_spans()]
    assert span_names.count("agent.run") == 1
    assert span_names.count("agent.step") == 2


def test_step_spans_are_children_of_the_run_span_in_the_same_trace():
    agent, exporter, provider = _traced_agent("traced-agent", [Step("only-step", lambda: {"ok": True})])

    agent.run()
    provider.force_flush()

    spans = exporter.get_finished_spans()
    run_span = next(s for s in spans if s.name == "agent.run")
    step_span = next(s for s in spans if s.name == "agent.step")

    assert step_span.context.trace_id == run_span.context.trace_id
    assert step_span.parent.span_id == run_span.context.span_id


def test_run_span_carries_the_run_id_attribute_matching_the_returned_run():
    agent, exporter, provider = _traced_agent("traced-agent", [Step("only-step", lambda: {"ok": True})])

    run = agent.run()
    provider.force_flush()

    run_span = next(s for s in exporter.get_finished_spans() if s.name == "agent.run")
    assert run_span.attributes["run_id"] == run.run_id
    assert run_span.attributes["run.status"] == "COMPLETED"


def test_a_failing_step_marks_both_its_own_span_and_the_run_span_as_error():
    def boom():
        raise ValueError("simulated failure")

    agent, exporter, provider = _traced_agent("traced-agent", [Step("boom-step", boom)])

    agent.run()
    provider.force_flush()

    spans = exporter.get_finished_spans()
    step_span = next(s for s in spans if s.name == "agent.step")
    run_span = next(s for s in spans if s.name == "agent.run")

    assert step_span.status.status_code == StatusCode.ERROR
    assert run_span.status.status_code == StatusCode.ERROR


def test_a_run_with_no_explicit_tracer_still_works_using_the_default_noop_tracer():
    # No tracer passed in — must not error even though nothing is recording.
    agent = DemoAgent(name="untraced-agent", steps=[Step("only-step", lambda: {"ok": True})])
    run = agent.run()

    assert run.status == "COMPLETED"

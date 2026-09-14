from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from observation_plane.ingest_exporter import ObservationStoreExporter


def _tracer(database_url):
    provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
    provider.add_span_processor(SimpleSpanProcessor(ObservationStoreExporter(database_url)))
    return provider, provider.get_tracer("test")


def test_a_real_span_lands_in_the_event_store_gated_and_normalized(pg_conn, database_url):
    provider, tracer = _tracer(database_url)

    with tracer.start_as_current_span("agent.run", attributes={"run_id": "run_ingest_1", "agent_name": "Test Agent"}):
        pass
    provider.force_flush()

    with pg_conn.cursor() as cur:
        cur.execute("SELECT name, attributes FROM observation_events WHERE attributes->>'run_id' = %s", ("run_ingest_1",))
        row = cur.fetchone()

    assert row is not None
    name, attributes = row
    assert name == "agent.run"
    assert attributes["agent_name"] == "Test Agent"


def test_an_attribute_not_on_the_allowlist_never_reaches_the_event_store(pg_conn, database_url):
    provider, tracer = _tracer(database_url)

    with tracer.start_as_current_span(
        "agent.run", attributes={"run_id": "run_ingest_2", "leaked_customer_email": "bob@example.com"}
    ):
        pass
    provider.force_flush()

    with pg_conn.cursor() as cur:
        cur.execute("SELECT attributes FROM observation_events WHERE attributes->>'run_id' = %s", ("run_ingest_2",))
        (attributes,) = cur.fetchone()

    assert "leaked_customer_email" not in attributes


def test_parent_child_spans_keep_their_relationship_through_the_exporter(pg_conn, database_url):
    provider, tracer = _tracer(database_url)

    with tracer.start_as_current_span("agent.run", attributes={"run_id": "run_ingest_3"}) as run_span:
        with tracer.start_as_current_span("agent.step", attributes={"step_name": "only-step"}):
            pass
        run_trace_id = format(run_span.get_span_context().trace_id, "032x")
        run_span_id = format(run_span.get_span_context().span_id, "016x")
    provider.force_flush()

    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT parent_span_id FROM observation_events WHERE trace_id = %s AND name = 'agent.step'",
            (run_trace_id,),
        )
        (parent_span_id,) = cur.fetchone()

    assert parent_span_id == run_span_id

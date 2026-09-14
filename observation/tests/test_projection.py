import uuid

from observation_plane.event_store import store_event
from observation_plane.privacy_gate import ObservationEvent
from observation_plane.projection import project_run


def _seed_run(conn, trace_id, *, status="COMPLETED", agent_name="Sales Research Agent", step_names=("retrieval", "model")):
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    root_span_id = uuid.uuid4().hex[:16]

    for name in step_names:
        store_event(
            conn,
            ObservationEvent(
                trace_id=trace_id,
                span_id=uuid.uuid4().hex[:16],
                parent_span_id=root_span_id,
                name="agent.step",
                start_time="2026-09-14T15:00:00",
                end_time="2026-09-14T15:00:00.500000",
                status="UNSET",
                attributes={"step_name": name},
            ),
        )

    # Root span stored LAST, exactly like real OTel export order (a span
    # only ends, and is only exported, after all its children have ended).
    store_event(
        conn,
        ObservationEvent(
            trace_id=trace_id,
            span_id=root_span_id,
            parent_span_id=None,
            name="agent.run",
            start_time="2026-09-14T15:00:00",
            end_time="2026-09-14T15:00:02.250000",
            status="UNSET",
            attributes={"run_id": run_id, "agent_name": agent_name, "run.status": status},
        ),
    )
    return run_id


def test_projects_a_completed_run_with_correct_step_count_and_duration(pg_conn):
    trace_id = uuid.uuid4().hex
    run_id = _seed_run(pg_conn, trace_id, status="COMPLETED", step_names=("retrieval", "model", "tool", "action"))

    projection = project_run(pg_conn, trace_id)

    assert projection is not None
    assert projection.run_id == run_id
    assert projection.status == "COMPLETED"
    assert projection.step_count == 4
    assert projection.duration_seconds == 2.25


def test_projects_a_failed_run_status(pg_conn):
    trace_id = uuid.uuid4().hex
    _seed_run(pg_conn, trace_id, status="FAILED", step_names=("retrieval",))

    projection = project_run(pg_conn, trace_id)

    assert projection.status == "FAILED"
    assert projection.step_count == 1


def test_unknown_trace_id_returns_none(pg_conn):
    assert project_run(pg_conn, uuid.uuid4().hex) is None


def test_projection_does_not_leak_steps_from_a_different_trace(pg_conn):
    trace_a = uuid.uuid4().hex
    trace_b = uuid.uuid4().hex
    _seed_run(pg_conn, trace_a, step_names=("a1", "a2"))
    _seed_run(pg_conn, trace_b, step_names=("b1", "b2", "b3"))

    projection_a = project_run(pg_conn, trace_a)
    projection_b = project_run(pg_conn, trace_b)

    assert projection_a.step_count == 2
    assert projection_b.step_count == 3

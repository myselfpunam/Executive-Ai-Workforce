import uuid

from observation_plane.event_store import store_event
from observation_plane.privacy_gate import ObservationEvent
from observation_plane.projection import list_recent_runs


def _seed_run(conn, status="COMPLETED"):
    trace_id = uuid.uuid4().hex
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    store_event(
        conn,
        ObservationEvent(
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=None,
            name="agent.run",
            start_time="2026-09-14T15:00:00",
            end_time="2026-09-14T15:00:01",
            status="UNSET",
            attributes={"run_id": run_id, "agent_name": "Sales Research Agent", "run.status": status},
        ),
    )
    return run_id


def test_lists_recently_seeded_runs(pg_conn):
    run_a = _seed_run(pg_conn)
    run_b = _seed_run(pg_conn)

    runs = list_recent_runs(pg_conn, limit=50)
    run_ids = [r.run_id for r in runs]

    assert run_a in run_ids
    assert run_b in run_ids


def test_most_recently_stored_run_comes_first(pg_conn):
    _seed_run(pg_conn)
    newest_run_id = _seed_run(pg_conn)

    runs = list_recent_runs(pg_conn, limit=50)

    assert runs[0].run_id == newest_run_id


def test_limit_is_respected(pg_conn):
    for _ in range(5):
        _seed_run(pg_conn)

    runs = list_recent_runs(pg_conn, limit=2)

    assert len(runs) == 2
